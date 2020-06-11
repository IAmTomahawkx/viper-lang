from .objects import PYK_Error

class PYK_RecursionError(PYK_Error):
    pass

class PYK_ExecutionError(PYK_Error):
    def init(self, msg=None):
        self.file = None
        self.lineno = None
        self.line = None
        self.msg = msg

class PYK_SyntaxError(PYK_ExecutionError):
    pass

class PYK_ArgumentError(PYK_ExecutionError):
    pass

class PYK_NameError(PYK_ExecutionError):
    pass

class PYK_StaticError(PYK_ExecutionError):
    pass
