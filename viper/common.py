from .errors import *
from .keywords import *

class VPNamespace(dict):
    __buildmode = False
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self[VIPER_KEYWORDS['VIPER_TRUE']] = True, True
        self[VIPER_KEYWORDS['VIPER_FALSE']] = False, True

    def buildmode(self, state: bool):
        self.__buildmode = state

    def force_assign(self, key: str, value, static: bool=False):
        dict.__setitem__(self, key, (value, static))
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def __getitem__(self, key):
        v = dict.__getitem__(self, key)
        try:
            return v[0]
        except:
            return v
        
    def __setitem__(self, key, value):
        static = False
        if isinstance(value, tuple):
            static = value[1]
            value = value[0]
        
        if self.__buildmode:
            return dict.__setitem__(self, key, (value, static))
        
        exists = dict.get(self, key, None)
        if exists is None:
            dict.__setitem__(self, key, (value, static))
        
        else:
            if exists[1]:
                raise VP_StaticError(key)
            
            dict.__setitem__(self, key, (value, static))
