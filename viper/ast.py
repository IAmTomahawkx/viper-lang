from typing import *
from .options import Configuration
import ast

__all__ = (
    "Tree",
    "LineHolder",
    "BlockHolder",
    "AST",
    "Operator",
    "Add",
    "Subtract",
    "Multiply",
    "Divide",
    "BoolOp",
    "And",
    "Or",
    "Argument",
    "Function",
    "Call",
    "For"
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

class LineHolder(AST):
    __slots__ = ("line",)

    def __init__(self, lineno: int, line: str):
        super().__init__(lineno)
        self.line = line

    def __str__(self):
        return f"<Lineholder line='{self.line}'>"

    __repr__ = __str__

class BlockHolder(AST):
    __slots__ = ("definer", "block")

    def __init__(self, lineno: int, definer: str, block: str):
        super().__init__(lineno)
        self.definer = definer
        self.block = block

    def __str__(self):
        return f"<Blockholder definer='{self.definer}' block='{self.block}'>"

    __repr__ = __str__

class Statement(AST):
    pass

class Assign(Statement):
    __slots__ = ("name", "value")

    def __init__(self, lineno: int, name: str, value: str):
        super().__init__(lineno)
        self.name = name
        self.value = value

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

    def __init__(self, lineno: int, left: str, right: str):
        super().__init__(lineno)
        self.left = left
        self.right = right

class And(BoolOp):
    pass

class Or(BoolOp):
    pass

class Argument(AST):
    __slots__ = ("name", "value", "optional")
    def __init__(self, lineno: int, name: str, value: str, optional: bool):
        super().__init__(lineno)
        self.name = name
        self.value = value
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

