from .objects import VP_Error

class VP_RecursionError(VP_Error):
    pass

class VP_ExecutionError(VP_Error):
    pass

class VP_SyntaxError(VP_ExecutionError):
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
    def __init__(self, message):
        self.message = message
        super(VP_RaisedError, self).__init__(message)

    def __repr__(self):
        return f"[Raised Error: {self.message}]"

    def __str__(self):
        return self.message