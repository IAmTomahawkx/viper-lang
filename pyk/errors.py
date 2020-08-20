from .objects import PYK_Error

class PYK_RecursionError(PYK_Error):
    pass

class PYK_ExecutionError(PYK_Error):
    pass

class PYK_SyntaxError(PYK_ExecutionError):
    pass

class PYK_ArgumentError(PYK_ExecutionError):
    pass

class PYK_NameError(PYK_ExecutionError):
    pass

class PYK_StaticError(PYK_ExecutionError):
    pass

class PYK_AttributeError(PYK_Error):
    pass

class PYK_RaisedError(PYK_Error):
    def __init__(self, message):
        self.message = message
        super(PYK_RaisedError, self).__init__(message)

    def __repr__(self):
        return f"[Raised Error: {self.message}]"

    def __str__(self):
        return self.message