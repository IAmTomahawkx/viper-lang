from .objects import PYKObject
from .common import PYKNamespace, find_outer_brackets
from .errors import PYK_SyntaxError, PYK_ArgumentError
from .keywords import PYK_KEYWORDS, PYK_BRACKETS

def interpret_arguments(raw_code: str):
    raw_code = find_outer_brackets(raw_code, PYK_BRACKETS['PYK_FUNCTIONARGS_IN'], PYK_BRACKETS['PYK_FUNCTIONARGS_OUT'], include_brackets=False)
    args = []
    
    argname = ""
    optional = False
    for char in raw_code:
        if char.isspace():
            continue
        
        if char == ",":
            if not argname:
                raise PYK_SyntaxError("Invalid comma")
            
            args.append((argname, optional))
            argname = ""
            optional = False
            continue
        
        if char == "?" and not argname:
            optional = True
            continue
        
        elif char == "?" and argname:
            raise PYK_SyntaxError("Invalid optional character, {0}".format(argname))
        
        argname += char
    
    if argname:
        args.append((argname, optional))
    
    return args

def get_function_name(raw_code):
    raw_code = raw_code.strip()
    name = ""
    for char in raw_code:
        if char == PYK_BRACKETS['PYK_FUNCTIONARGS_IN']:
            break
        
        name += char
    
    if not name:
        raise PYK_SyntaxError("No function name")
    
    return name.strip()

class PYKFunction(PYKObject):
    __slots__ = ("raw_code", "code", "_code", "file", "global_ns")
    def __init__(self, raw_code: str, fp: str, namespace: PYKNamespace):
        self.raw_code = raw_code
        code = raw_code.replace(PYK_KEYWORDS['PYK_FUNC'], "", 1)
        code = code.strip()
        self.name = get_function_name(code)
        code = code.replace(self.name, "", 1).strip()
        self.file = fp
        self.arguments = interpret_arguments(code)
        self.code = find_outer_brackets(code, skip_extra=True)
        self._code = find_outer_brackets(code, skip_extra=True, include_brackets=False)
        self.global_ns = namespace
        self.init()
    
    def Call(self, *args, depth=None):
        if depth is None:
            raise ValueError("depth is a required argument")
        
        ns = PYKNamespace()
        ns.buildmode(True)
        for index, (name, optional) in enumerate(self.arguments):
            try:
                ns[name] = args[index]
            except IndexError:
                if optional:
                    break
                raise PYK_ArgumentError("Missing required argument '{0}' for function call".format(name))
        
        ns.buildmode(False)
        resp = parser.build_code(self._code, self.global_ns, ns, self.file, depth+1)
        return resp

from . import parser
