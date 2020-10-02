VP_NONE = None

class VPObject:
    __static = False
    def __init__(self, *args, **kwargs):
        self.init(*args, **kwargs)
    
    def init(self, *args, **kwargs):
        pass


class _VP_NULL(VPObject):
    __slots__ = tuple()
    def __new__(cls):
        global VP_NONE
        if VP_NONE is not None:
            return VP_NONE
        
        VP_NONE = object.__new__(cls)
        return VP_NONE
    
    def __str__(self):
        return "null"
    
    __repr__ = __str__

_VP_NULL()

class PyVP_Model:
    def __dir__(self):
        dirs = super(PyVP_Model, self).__dir__()
        dirs = [d for d in dirs if not d.startswith("_")] # hide attributes that cant be accessed
        return dirs