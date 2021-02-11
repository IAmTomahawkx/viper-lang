import functools
import inspect
from typing import *
from . import objects, errors

if TYPE_CHECKING:
    from .runner import Runtime
    from .objects import VPObject


class dummy:
    __slots__ = "lineno", "type", "index"

    def __init__(self, lineno, type, index):
        self.lineno = lineno
        self.type = type
        self.index = index

    def __repr__(self):
        return f"<DummyToken lineno={self.lineno} type={self.type}>"


class Block(list):
    def __init__(self, lineno, index):
        super().__init__()
        self.type = "BLOCK"
        self.lineno = lineno
        self.index = index


class ASTBase:
    __slots__ = "lineno", "offset"

    def __init__(self, lineno: int, offset: int):
        self.lineno = lineno
        self.offset = offset

    def __str__(self):
        return f"[{self.__class__.__name__} lineno={self.lineno if hasattr(self, 'lineno') else None} {' '.join(f'{a}={getattr(self, a)}' for a in self.__slots__)}]"

    __repr__ = __str__

    async def execute(self, runner: "Runtime"):
        pass


class Identifier(ASTBase):
    __slots__ = ('name',)
    cls_name = "identifier"

    def __init__(self, name: str, lineno: int, offset: int):
        super().__init__(lineno, offset)
        self.name = name

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and other.name == self.name

    def __hash__(self):
        return self.name.__hash__()

    def transform_to_string(self):
        return self.name

    def get_top_level_name(self):
        return self

    async def execute(self, runner: "Runtime"):
        return await runner.get_variable(self)


class Assignment(ASTBase):
    __slots__ = "name", "value", "static"

    def __init__(self, name: Identifier, value: ASTBase, lineno: int, offset: int,
                 static=False):
        self.name = name
        self.value = value
        self.static = static
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        await runner.set_variable(self.name, await self.value.execute(runner), self.static)

class Cast(ASTBase):
    __slots__ = "name", "caster"

    def __init__(self, name: Identifier, caster: Identifier, lineno: int, offset: int):
        self.name = name
        self.caster = caster
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        caster = await runner.get_variable(self.caster)
        if not issubclass(caster, objects.Primary) and not isinstance(caster, objects.Primary):
            raise errors.ViperExecutionError(runner, self.name.lineno, f"Expected to cast to a basic type (string, "
                                                                       f"integer, bool), got '{caster}'")

        name = await runner.get_variable(self.name)
        if not name.__getattribute__("_cast"):
            raise errors.ViperExecutionError(runner, self.name.lineno, f"cannot use cast on {name}")

        return name.__getattribute__("_cast")(caster, self.lineno)

class Attribute(ASTBase):
    __slots__ = "parent", "child", "appended_children"

    def __init__(self, parent: Identifier, child: Identifier, lineno: int, offset: int,
                 appended_children: List[Identifier] = None):
        self.parent = parent
        self.child = child
        self.appended_children = appended_children
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime", parent: Identifier = None):
        if not self.parent and not parent:
            raise ValueError("no parent given")

        parent = parent or self.parent
        parent = await runner.get_variable(parent)
        result = getattr(parent, self.child.name, None)

        if result is None:
            raise errors.ViperAttributeError(runner, self.lineno, parent, self.child)

        if self.appended_children:
            for child in self.appended_children:
                result = getattr(result, child.name, None)

                if result is None:
                    raise errors.ViperAttributeError(runner, self.lineno, result, self.child)

        return result


class Argument(ASTBase):
    __slots__ = "name", "optional", "default", "position"

    def __init__(self, name: Identifier, optional: bool, position: int, lineno: int, offset: int,
                 default: objects.Primary = None):
        self.name = name
        self.optional = optional
        self.default = default
        self.position = position
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime", maybe_arg: Optional["CallArgument"]) -> Optional[objects.VPObject]:
        if maybe_arg is None and self.default:
            return self.default
        elif maybe_arg is None and self.optional:
            return runner.null
        elif maybe_arg is None:
            return None

        if isinstance(maybe_arg.value, PrimaryWrapper):
            return await maybe_arg.execute(runner)

        return await runner.get_variable(maybe_arg.value)

    def __eq__(self, other):
        return isinstance(other, Argument) and other.name == self.name and other.optional == self.optional


class CallArgument(ASTBase):
    __slots__ = "position", "value", "index", "type"

    def __init__(self, position: int, value: Union[ASTBase, objects.Primary], lineno: int, offset: int):
        self.position = position
        self.value = value
        self.index = -1
        self.type = "IDENTIFIER"
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        if isinstance(self.value, objects.Primary):
            return self.value

        return await self.value.execute(runner)


class Function(ASTBase):
    __slots__ = "code", "arguments", "static", "name", "matches"

    def __init__(self, name: Identifier, code: List[ASTBase], arguments: List[Argument], static: bool, lineno: int,
                 offset: int):
        self.code = code
        self.arguments = arguments
        self.static = static
        self.name = name
        self.matches: List[objects.Function] = []
        super().__init__(lineno, offset)

    def _find(self, pos, args):
        for arg in args:
            if arg.position == pos:
                return arg

    async def execute(self, runner: "Runtime", args: List[CallArgument]) -> "VPObject":
        for match in self.matches:
            aln = len(args)
            min_args = sum((1 for a in match._ast.arguments if not a.optional))
            max_args = len(match._ast.arguments)
            if min_args <= aln <= max_args:
                return await match._ast._actual_execute(runner, args)

        raise errors.ViperExecutionError(runner, self.lineno, f"function {self.name.name} could not take such arguments: {', '.join((str(x) for x in args))}")

    async def _actual_execute(self, runner: "Runtime", args: List[CallArgument]) -> "VPObject":
        with runner.new_scope():
            for arg in self.arguments:
                _arg = self._find(arg.position, args)
                value = await arg.execute(runner, _arg)
                if value is None:
                    raise errors.ViperExecutionError(runner, self.lineno, f"No value passed for argument '{arg.name}'")
                elif isinstance(value, objects.Primary):
                    value = value._copy() # make them immutable

                await runner.set_variable(arg.name, value, False)

            return await runner._run_function_body(self.code)


class FunctionCall(ASTBase):
    __slots__ = "name", "args"

    def __init__(self, name: Union[Identifier, Attribute], args: List[CallArgument], lineno: int, offset: int):
        self.name = name
        self.args = args
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        func = await self.name.execute(runner)
        if isinstance(func, objects.Function):
            return await func.__getattribute__("_call")(runner, self.args)

        elif isinstance(func, objects.PyNativeObjectWrapper):
            caller = object.__getattribute__(func, "_call")
            args = []
            for arg in self.args:
                args.append(await arg.execute(runner))
            return await caller(runner, self.lineno, *args)

        elif inspect.isfunction(func) or inspect.ismethod(func):
            # must be an internal function, it shouldn't need wrapped stuff. so pass a line number and the args
            args = []
            for arg in self.args:
                args.append(await arg.execute(runner))

            return await func(runner, self.lineno, *args)

        else:
            raise errors.ViperExecutionError(runner, self.name.lineno, f"{func} is not callable")


class If(ASTBase):
    __slots__ = "condition", "code", "others", "finish"

    def __init__(self, condition: "BiOperatorExpr", block: List[Any], lineno: int, offset: int):
        self.condition = condition
        self.code = block
        self.others: List["ElseIf"] = []
        self.finish: Optional["Else"] = None
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        passing = await self.condition.execute(runner)
        if passing:
            return await runner._run_function_body(self.code)

        for elseif in self.others:
            if await elseif.condition.execute(runner):
                return await runner._run_function_body(self.code)

        if self.finish:
            return await runner._run_function_body(self.finish.code)


class ElseIf(ASTBase):
    __slots__ = "condition", "code"

    def __init__(self, condition: "BiOperatorExpr", block: List[Any], lineno: int, offset: int):
        self.condition = condition
        self.code = block
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        passing = await self.condition.execute(runner)
        if passing:
            return await runner._run_function_body(self.code)


class Else(ASTBase):
    __slots__ = "code",

    def __init__(self, code: List[Any], lineno: int, offset: int):
        self.code = code
        super().__init__(lineno, offset)

class PrimaryWrapper(ASTBase):
    __slots__ = "wraps", "obj"
    def __init__(self, wraps: Type, obj: Any, lineno: int, offset: int):
        self.wraps = wraps
        self.obj = obj
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        return self.wraps(self.obj, self.lineno, runner)

class Import(ASTBase):
    __slots__ = "module",
    def __init__(self, module: Identifier, lineno: int, offset: int):
        self.module = module
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        return await runner.import_module(self.module, self.module.lineno)

class Try(ASTBase):
    __slots__ = "code", "catch"
    def __init__(self, code: List[Any], lineno: int, offset: int):
        self.code = code
        self.catch: Optional["Catch"] = None
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        try:
            await runner._common_execute(self.code)
        except errors.ViperRaisedError as e:
            if self.catch is not None:
                await runner.set_variable(Identifier("error", -1, -1), objects.String(e.message, -1, runner), True)
                await runner._common_execute(self.catch.code)
                runner.scope.del_variable(runner, Identifier("error", -1, -1))


class Catch(ASTBase):
    __slots__ = "code",
    def __init__(self, code: List[Any], lineno: int, offset: int):
        self.code = code
        super().__init__(lineno, offset)

class Throw(ASTBase):
    __slots__ = "expr",
    def __init__(self, expr: Any, lineno: int, offset: int):
        self.expr = expr
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        value = await self.expr.execute(runner)
        if not isinstance(value, objects.String):
            raise errors.ViperTypeError(runner, self.expr.lineno, f"Expected String, got {value}")

        raise errors.ViperRaisedError(runner, self.expr.lineno, value._value)

class Operator:
    __slots__ = ()

    def __repr__(self):
        return '{0.__class__.__name__}()'.format(self)


# math

class Plus(Operator):
    pass


class Minus(Operator):
    pass


class Times(Operator):
    pass


class Divide(Operator):
    pass


class Modulus(Operator):
    pass


class Range(Operator):
    pass


# equality

class EqualTo(Operator):
    pass


class NotEqualTo(Operator):
    pass


class GreaterThan(Operator):
    pass


class GreaterOrEqual(Operator):
    pass


class LessThan(Operator):
    pass


class LessOrEqual(Operator):
    pass

def unwrap_wrapped(func):
    @functools.wraps(func)
    def wrapped(self, runner, l, r):
        _l = l
        _r = r
        if isinstance(l, objects.Primary):
            l = l._value
        if isinstance(r, objects.Primary):
            r = r._value

        resp = func(self, l, r)
        if isinstance(_l, objects.Primary):
            return _l.__class__(resp, self.lineno, runner)
        if not isinstance(resp, objects.VPObject):
            return objects.PyObjectWrapper(runner, resp)
        return resp
    return wrapped

class BiOperatorExpr(ASTBase):
    __slots__ = ('left', 'op', 'right')

    def __init__(self, left: ASTBase, op: Any, right: ASTBase, lineno: int, offset: int):
        self.left = left
        self.op = op
        self.right = right
        super().__init__(lineno, offset)

    @unwrap_wrapped
    def _Plus(self, l, r):
        return l + r

    @unwrap_wrapped
    def _Minus(self, l, r):
        return l - r

    @unwrap_wrapped
    def _Times(self, l, r):
        return l * r

    @unwrap_wrapped
    def _Divide(self, l, r):
        return l // r

    @unwrap_wrapped
    def _Modulus(self, l, r):
        return l % r

    @unwrap_wrapped
    def _EqualTo(self, l, r):
        return l == r

    @unwrap_wrapped
    def _NotEqualTo(self, l, r):
        return l != r

    @unwrap_wrapped
    def _GreaterThan(self, l, r):
        return l > r

    @unwrap_wrapped
    def _GreaterOrEqual(self, l, r):
        return l >= r

    @unwrap_wrapped
    def _LessThan(self, l, r):
        return l < r

    @unwrap_wrapped
    def _LessOrEqual(self, l, r):
        return l <= r

    def _Cast(self, l, r):
        return l._cast(r, -1)

    async def execute(self, runner: "Runtime"):
        left = await runner.get_variable(self.left) if isinstance(self.left, Identifier) else await self.left.execute(runner)
        right = await runner.get_variable(self.right) if isinstance(self.right, Identifier) else await self.right.execute(
            runner)

        return getattr(self, '_' + self.op.__name__)(runner, left, right)
