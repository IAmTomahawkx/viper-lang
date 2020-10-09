from typing import *
from .options import Configuration
import ast

__all__ = (
    "Tree",
    "LineHolder",
    "BlockHolder",
    "AST",
    "Assignment",
    "PlusEquals",
    "MinusEquals",
    "TimesEquals",
    "DivEquals",
    "Reference",
    "Operator",
    "Add",
    "Subtract",
    "Multiply",
    "Divide",
    "BoolOp",
    "And",
    "Or",
    "Equals",
    "NotEquals",
    "Greater",
    "GreaterEquals",
    "Lesser",
    "LesserEquals",
    "Contains",
    "NotContains",
    "If",
    "ElseIf",
    "Else",
    "Argument",
    "Function",
    "Call",
    "For",
    "Return",
    "Literal",
    "String",
    "Int",
    "Bool",
    "Raise"
)

class Tree:
    __slots__ = ("configuration", "source", "parsed", "filename")

    def __init__(self, config: Configuration, filename: str, source: str):
        self.configuration: Configuration = config
        self.source: str = source
        self.filename: str = filename
        self.parsed: List[AST] = []

class AST:
    __slots__ = ("lineno",)

    def __init__(self, lineno: int):
        self.lineno = lineno

    def __repr__(self):
        items = " ".join([f"{a}={getattr(self, a)}" for a in self.__slots__])
        return f"[{self.__class__.__name__} {items}]"

class LineHolder(AST):
    __slots__ = ("line",)

    def __init__(self, lineno: int, line: str):
        super().__init__(lineno)
        self.line = line

    def __str__(self):
        return f"<Lineholder line='{self.line}' line={self.lineno}>"

    __repr__ = __str__

class BlockHolder(AST):
    __slots__ = ("definer", "block")

    def __init__(self, lineno: int, definer: str, block: str):
        super().__init__(lineno)
        self.definer = definer
        self.block = block

    def __str__(self):
        return f"<Blockholder definer='{self.definer}' block='{self.block}' line={self.lineno}>"

    __repr__ = __str__

class Statement(AST):
    pass

class Assignment(Statement):
    __slots__ = ("name", "value", "static")

    def __init__(self, lineno: int, static: bool, name: str, value: AST):
        super().__init__(lineno)
        self.name = name
        self.value = value
        self.static = static

class PlusEquals(Statement):
    __slots__ = ("target", "value")

    def __init__(self, lineno: int, target: str, value: AST):
        super().__init__(lineno)
        self.target = target
        self.value = value

class MinusEquals(Statement):
    __slots__ = ("target", "value")

    def __init__(self, lineno: int, target: str, value: AST):
        super().__init__(lineno)
        self.target = target
        self.value = value

class TimesEquals(Statement):
    __slots__ = ("target", "value")

    def __init__(self, lineno: int, target: str, value: AST):
        super().__init__(lineno)
        self.target = target
        self.value = value

class DivEquals(Statement):
    __slots__ = ("target", "value")

    def __init__(self, lineno: int, target: str, value: AST):
        super().__init__(lineno)
        self.target = target
        self.value = value

class Reference(AST):
    __slots__ = ("variable",)

    def __init__(self, lineno: int, variable: str):
        super().__init__(lineno)
        self.variable = variable

class Operator(AST):
    __slots__ = ("left", "right")

    def __init__(self, lineno: int, left: str, right: str):
        super().__init__(lineno)
        self.left = left
        self.right = right

class Add(Operator):
    pass

class Subtract(Operator):
    pass

class Multiply(Operator):
    pass

class Divide(Operator):
    pass

class BoolOp(AST):
    __slots__ = ("left", "right")

    def __init__(self, lineno: int, left: AST, right: Optional[AST]):
        super().__init__(lineno)
        self.left = left
        self.right = right

class Equals(BoolOp):
    pass

class NotEquals(BoolOp):
    pass

class Greater(BoolOp):
    pass

class Lesser(BoolOp):
    pass

class GreaterEquals(BoolOp):
    pass

class LesserEquals(BoolOp):
    pass

class Contains(BoolOp):
    pass

class NotContains(BoolOp):
    pass

class And(BoolOp):
    pass

class Or(BoolOp):
    pass

class Argument(AST):
    __slots__ = ("name", "optional")
    def __init__(self, lineno: int, name: str, optional: bool):
        super().__init__(lineno)
        self.name = name
        self.optional = optional

class Function(AST):
    __slots__ = ("code", "lineno", "args")
    def __init__(self, lineno: int, code: str, args: List[Argument]):
        super().__init__(lineno)
        self.code = code
        self.args = args

class Call(AST):
    __slots__ = ("item",)
    def __init__(self, lineno: int, item: str):
        super().__init__(lineno)
        self.item = item

class For(AST):
    __slots__ = ("iterable", "variable")

    def __init__(self, lineno: int, iterable: str, variable: str):
        super().__init__(lineno)
        self.iterable = iterable
        self.variable = variable

class If(AST):
    __slots__ = ("condition", "code", "elif_", "else_")

    def __init__(self, lineno: int, condition: BoolOp, code: List[AST], elifs: List[List["ElseIf"]], else_: Optional["Else"]):
        super().__init__(lineno)
        self.condition = condition
        self.code = code
        self.elif_ = elifs
        self.else_ = else_

class ElseIf(AST):
    __slots__ = ("condition", "code")

    def __init__(self, lineno: int, condition: BoolOp, code: List[AST]):
        super().__init__(lineno)
        self.condition = condition
        self.code = code

class Else(AST):
    __slots__ = ("code",)

    def __init__(self, lineno: int, code: List[AST]):
        super().__init__(lineno)
        self.code = code

class Return(AST):
    __slots__ = ("items",)

    def __init__(self, lineno: int, items: List[AST]):
        super().__init__(lineno)
        self.items = items

class Literal(AST):
    __slots__ = ("value",)

    def __init__(self, lineno: int, value: Any):
        super().__init__(lineno)
        self.value = value

class String(Literal):
    pass

class Int(Literal):
    pass

class Bool(Literal):
    pass

class Raise(AST):
    __slots__ = ("message",)

    def __init__(self, lineno: int, message: List[AST]):
        super().__init__(lineno)
        self.message = message