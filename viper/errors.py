from typing import *

__all__ = (
    "VP_Error",
    "VP_RecursionError",
    "VP_ExecutionError",
    "VP_SyntaxError",
    "VP_ArgumentError",
    "VP_NameError",
    "VP_StaticError",
    "VP_AttributeError",
    "VP_RaisedError"
)

class VP_Error(Exception):
    message: Optional[str]
    tree: "Tree"
    line: int
    message: Optional[AnyStr]

    def __init__(self, tree: "Tree", line: int, *args: Any, **kwargs: Any):
        self.tree = tree
        self.line = line
        self.init(*args, **kwargs)
        super().__init__(*args)

    def init(self, *args: List[Any], **kwargs: Dict[Hashable, Any]) -> None:
        if args:
            self.message = args[0] if isinstance(args[0], str) else repr(args[0])
        else:
            self.message = None

    def __str__(self) -> str:
        return f"Line {self.line}, {self.message}\n\t{self.tree.source.splitlines()[self.line-1]}"

    def format_stack(self) -> str:
        pass # TODO

class VP_RecursionError(VP_Error):
    pass

class VP_ExecutionError(VP_Error):
    pass

class VP_SyntaxError(VP_Error):
    pass

class VP_ArgumentError(VP_ExecutionError):
    pass

class VP_NameError(VP_ExecutionError):
    pass

class VP_StaticError(VP_ExecutionError):
    pass

class VP_AttributeError(VP_Error):
    pass

class VP_RaisedError(VP_Error):
    def init(self, tree: "Tree", line: int, msg: str):
        super().__init__(tree, line, msg)

    def __repr__(self):
        return f"[Raised Error: {self.message}]"

    def __str__(self):
        return self.message

from .ast import Tree