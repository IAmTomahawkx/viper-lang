from .objects import VPObject, VP_NONE
from .common import VPNamespace, find_outer_brackets
from .errors import VP_SyntaxError, VP_ArgumentError
from .keywords import VIPER_KEYWORDS, VIPER_BRACKETS

def interpret_arguments(raw_code: str):
    raw_code = find_outer_brackets(raw_code, VIPER_BRACKETS['VIPER_FUNCTIONARGS_IN'], VIPER_BRACKETS['VIPER_FUNCTIONARGS_OUT'], include_brackets=False)
    args = []
    
    argname = ""
    optional = False
    for char in raw_code:
        if char.isspace():
            continue
        
        if char == ",":
            if not argname:
                raise VP_SyntaxError("Invalid comma")
            
            args.append((argname, optional))
            argname = ""
            optional = False
            continue
        
        if char == "?" and not argname:
            optional = True
            continue
        
        elif char == "?" and argname:
            raise VP_SyntaxError("Invalid optional character, {0}".format(argname))
        
        argname += char
    
    if argname:
        args.append((argname, optional))
    
    return args

def get_function_name(raw_code):
    raw_code = raw_code.strip()
    name = ""
    for char in raw_code:
        if char == VIPER_BRACKETS['VIPER_FUNCTIONARGS_IN']:
            break
        
        name += char
    
    if not name:
        raise VP_SyntaxError("No function name")
    
    return name.strip()

class VPFunction(VPObject):
    __slots__ = ("raw_code", "code", "_code", "file", "global_ns")
    def __init__(self, raw_code: str, fp: str, namespace: VPNamespace):
        self.raw_code = raw_code
        code = raw_code.replace(VIPER_KEYWORDS['VIPER_FUNC'], "", 1)
        code = code.strip()
        self.name = get_function_name(code)
        code = code.replace(self.name, "", 1).strip()
        self.file = fp
        self.arguments = interpret_arguments(code)
        self.code = find_outer_brackets(code, skip_extra=True)
        self._code = find_outer_brackets(code, skip_extra=True, include_brackets=False)
        self.global_ns = namespace
        self.init()

    def __repr__(self):
        return "<Function {0} in file {1}>".format(self.name, self.file)
    
    async def Call(self, *args, depth=None):
        args = list(reversed(args))
        if depth is None:
            raise ValueError("depth is a required argument")
        
        ns = VPNamespace()
        ns.buildmode(True)
        for index, (name, optional) in enumerate(self.arguments):
            try:
                ns[name] = args.pop()
            except:
                if optional:
                    ns[name] = VP_NONE
                    break
                raise VP_ArgumentError("Missing required argument '{0}' for function call".format(name))

        if args:
            raise VP_ArgumentError("Too many arguments passed to " + self.name)
        
        ns.buildmode(False)
        resp = await parser.build_code_async(self._code, self.global_ns, ns, self.file, depth+1, func=self)
        return resp

from . import parser
