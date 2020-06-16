from .errors import *
from .keywords import *

class PYKNamespace(dict):
    __buildmode = False
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self[PYK_KEYWORDS['PYK_TRUE']] = True, True
        self[PYK_KEYWORDS['PYK_FALSE']] = False, True

    def buildmode(self, state: bool):
        self.__buildmode = state
    
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
                raise PYK_StaticError(key)
            
            dict.__setitem__(self, key, (value, static))

def find_outer_brackets(
    raw_code: str,
    bracket_in: str = None,
    bracket_out: str = None,
    include_brackets: bool = True,
    skip_extra: bool = False
    ) -> str:
    """
    returns code up to the outermost bracket
    """
    bracket_in = bracket_in or PYK_BRACKETS['PYK_CODE_IN']
    bracket_out = bracket_out or PYK_BRACKETS['PYK_CODE_OUT']
    
    raw_code = raw_code.strip()
    iterator = iter(raw_code)
    output = ""
    level = 0
    
    if not raw_code.startswith(bracket_in):
        if not skip_extra:
            raise PYK_SyntaxError("Start character, '{0}', not found".format(bracket_in))
        
        else:
            char = next(iterator)
            try:
                while char != bracket_in:
                    char = next(iterator)
                
                if include_brackets:
                    output += bracket_in
                level += 1
            except StopIteration:
                raise PYK_SyntaxError("Start character, '{0}', not found".format(bracket_in))
    
    for char in iterator:
        if include_brackets:
            output += char
        
        if char == bracket_in:
            level += 1
            if level != 1:
                output += char
            
            continue
        
        if char == bracket_out:
            level -= 1
            if level == 0:
                return output
        
        if not include_brackets:
            output += char
    
    raise PYK_SyntaxError("End character, '{0}', not found".format(bracket_out))
