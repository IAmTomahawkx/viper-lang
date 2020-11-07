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
        return runner.get_current_scope().get_variable(self)


class Assignment(ASTBase):
    __slots__ = "name", "value", "static"

    def __init__(self, name: Identifier, value: Union[ASTBase, objects.Primary], lineno: int, offset: int,
                 static=False):
        self.name = name
        self.value = value
        self.static = static
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        if isinstance(self.value, ASTBase):
            runner.set_var(self.name, self.value.execute(runner))
        else:
            runner.set_var(self.name, self.value)


class Cast(ASTBase):
    __slots__ = "name", "caster"

    def __init__(self, name: str, caster: objects.Primary, lineno: int, offset: int):
        self.name = name
        self.caster = caster
        super().__init__(lineno, offset)


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
        parent = runner.get_variable(parent)
        result = getattr(parent, self.child.name, None)

        if result is None:
            raise errors.ViperAttributeError(runner, self.lineno, parent, self.child)

        if self.appended_children:
            for child in self.appended_children:
                result = getattr(parent, child.name, None)

                if result is None:
                    raise errors.ViperAttributeError(runner, self.lineno, parent, self.child)

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

        if isinstance(maybe_arg.value, objects.Primary):
            return maybe_arg.value

        return runner.get_variable(maybe_arg.value)


class CallArgument(ASTBase):
    __slots__ = "position", "value"

    def __init__(self, position: int, value: Union[ASTBase, objects.Primary], lineno: int, offset: int):
        self.position = position
        self.value = value
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        if isinstance(self.value, objects.Primary):
            return self.value

        return await self.value.execute(runner)


class Function(ASTBase):
    __slots__ = "code", "arguments", "static", "name"

    def __init__(self, name: Identifier, code: List[ASTBase], arguments: List[Argument], static: bool, lineno: int,
                 offset: int):
        self.code = code
        self.arguments = arguments
        self.static = static
        self.name = name
        super().__init__(lineno, offset)

    def _find(self, pos, args):
        for arg in args:
            if arg.position == pos:
                return pos

    async def execute(self, runner: "Runtime", args: List[CallArgument]) -> "VPObject":
        with runner.new_scope():
            for arg in self.arguments:
                _arg = self._find(arg.position, args)
                value = await arg.execute(runner, _arg)
                if value is None:
                    raise errors.ViperExecutionError(runner, self.lineno, f"No value passed for argument '{arg.name}'")

                runner.set_variable(arg.name, value)

            return await runner._run_function_body(self.code)


class FunctionCall(ASTBase):
    __slots__ = "name", "args"

    def __init__(self, name: Identifier, args: List[CallArgument], lineno: int, offset: int):
        self.name = name
        self.args = args
        super().__init__(lineno, offset)

    async def execute(self, runner: "Runtime"):
        func = runner.get_variable(self.name)
        return await func.execute(runner, self.args)


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
            return await runner._run_function_body(self.block)

        for elseif in self.others:
            if await elseif.condition.execute(runner):
                return await runner._execute_function_body(self.code)

        if self.finish:
            return await runner._execute_function_body(self.finish.code)


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
    __slots__ = "code"

    def __init__(self, code: List[Any], lineno: int, offset: int):
        self.code = code
        super().__init__(lineno, offset)


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


class BiOperatorExpr(ASTBase):
    __slots__ = ('left', 'op', 'right')

    def __init__(self, left: ASTBase, op: Any, right: ASTBase, lineno: int, offset: int):
        self.left = left
        self.op = op
        self.right = right
        super().__init__(lineno, offset)

    def _Plus(self, l, r):
        return l + r

    def _Minus(self, l, r):
        return l - r

    def _Times(self, l, r):
        return l * r

    def _Divide(self, l, r):
        return l // r

    def _Modulus(self, l, r):
        return l % r

    def _EqualTo(self, l, r):
        return l == r

    def _NotEqualTo(self, l, r):
        return l != r

    def _GreaterThan(self, l, r):
        return l > r

    def _GreaterOrEqual(self, l, r):
        return l >= r

    def _LessThan(self, l, r):
        return l < r

    def _LessOrEqual(self, l, r):
        return l <= r

    def _Cast(self, l, r):
        return l._cast(r)

    async def execute(self, runner: "Runtime"):
        left = runner.get_variable(self.left) if isinstance(self.left, Identifier) else await self.left.execute(runner)
        right = runner.get_variable(self.right) if isinstance(self.right, Identifier) else await self.right.execute(
            runner)

        return getattr(self, '_' + self.op.__class__.__name__)(left, right)
