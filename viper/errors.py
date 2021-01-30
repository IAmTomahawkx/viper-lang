from typing import *
from sly.lex import Token

__all__ = (
    "ViperError",
    "ViperRecursionError",
    "ViperExecutionError",
    "ViperSyntaxError",
    "ViperArgumentError",
    "ViperNameError",
    "ViperStaticError",
    "ViperAttributeError",
    "ViperRaisedError"
)

class ViperError(Exception):
    message: Optional[str]
    runner: Any
    line: int
    message: Optional[AnyStr]

    def __init__(self, runner, line: int, *args: Any, **kwargs: Any):
        self.runner = runner
        self.line = line
        self.init(*args, **kwargs)
        super().__init__(*args)

    def init(self, *args: List[Any], **kwargs: Dict[Hashable, Any]) -> None:
        if args:
            self.message = args[0] if isinstance(args[0], str) else repr(args[0])
        else:
            self.message = None

#    def __str__(self) -> str:
#        return f"Line {self.line}, {self.message}\n\t{self.tree.source.splitlines()[self.line-1]}"

    def format_stack(self) -> str:
        pass # TODO

class ViperRecursionError(ViperError):
    pass

class ViperExecutionError(ViperError):
    pass

class ViperSyntaxError(ViperError):
    def __init__(self, token: Token, offset: int, msg: str):
        self._token = token
        self._offset = offset
        self.message = msg

    def __str__(self):
        return f"<line {self._token.lineno}, offset {self._offset}, token '{self._token.value.strip()}': {self.message}>"

class ViperArgumentError(ViperExecutionError):
    pass

class ViperNameError(ViperExecutionError):
    pass

class ViperStaticError(ViperExecutionError):
    pass

class ViperAttributeError(ViperError):
    def __init__(self, runner, line: int, parent, child):
        self.parent = parent
        self.child = child
        super(ViperAttributeError, self).__init__(runner, line, f"{parent} has no attribute {child.name}")

class ViperRaisedError(ViperError):
    pass

    def __repr__(self):
        return f"[Raised Error: {self.message}]"

    def __str__(self):
        return self.message

class ViperCastError(ViperError):
    pass

class ViperTypeError(ViperError):
    pass

class ViperModuleError(ViperError):
    pass