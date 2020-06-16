from .keywords import PYK_KEYWORDS

PYK_NONE = None

class PYKObject:
    __static = False
    def __init__(self, *args, **kwargs):
        self.init(*args, **kwargs)
    
    def init(self, *args, **kwargs):
        pass


class _PYK_NULL(PYKObject):
    __slots__ = tuple()
    def __new__(cls):
        global PYK_NONE
        if PYK_NONE is not None:
            return PYK_NONE
        
        PYK_NONE = object.__new__(cls)
        return PYK_NONE
    
    def __str__(self):
        return "null"
    
    __repr__ = __str__

_PYK_NULL()


class PYK_Error(Exception):
    def __init__(self, *args, **kwargs):
        self.init(*args, **kwargs)
        super().__init__(*args, **kwargs)
    
    def init(self, msg):
        self.message = msg if isinstance(msg, str) else repr(msg)


class PYK_LIST(PYKObject):
    pass