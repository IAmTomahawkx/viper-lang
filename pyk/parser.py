import inspect

from .keywords import PYK_BRACKETS, PYK_STRICT_PARSING_KEYWORDS, PYK_KEYWORDS
from .errors import *
from .objects import *
from .common import *
from . import functions

async def get_value_from_string(raw: str, global_ns, local_ns, depth):
    raw = raw.strip()

    if any([x in raw for x in "/*+-"]):
        return await build_math(raw, global_ns, local_ns, depth) # put this above the string parsing to allow string adding

    if raw.startswith('"'):
        # its a string
        resp = ""
        depth = False
        skip_one = False
        for index, char in enumerate(raw):
            if skip_one:
                skip_one = False
                continue
            
            if char == "\\":
                try:
                    resp += raw[index+1]
                    skip_one = True
                    continue
                except:
                    raise PYK_SyntaxError("Invalid escape")
            
            if char == '"':
                if depth:
                    return resp
                depth = True
                continue
            if depth:
                resp += char

        raise PYK_SyntaxError("Invalid string")

    
    if raw.startswith(PYK_KEYWORDS['PYK_VARMARKER']):
        var = get_variable(raw, global_ns, local_ns)
        return var
    
    if raw == PYK_KEYWORDS['PYK_TRUE']:
        return True
    
    if raw == PYK_KEYWORDS['PYK_FALSE']:
        return False
    
    if raw == PYK_KEYWORDS['PYK_NULL']:
        return PYK_NONE
    
    if not raw.isalpha():
        try:
            return int(raw)
        except:
            try:
                return float(raw)
            except:
                pass
    
    if PYK_BRACKETS['PYK_FUNCTIONCALL_IN'] in raw:
        return await call_function(raw, global_ns, local_ns, depth)
    
    if local_ns is not None:
        var = local_ns.get(raw)
        if var is not None:
            return var
    
    var = global_ns.get(raw)
    if var is not None:
        return var
    
    raise PYK_NameError(raw)

def get_variable_name(raw: str, marker=None):
    name = ""
    if raw in [PYK_KEYWORDS['PYK_TRUE'], PYK_KEYWORDS['PYK_FALSE']]:
        return raw
    
    marker = marker or PYK_KEYWORDS['PYK_VARMARKER']
    for index, char in enumerate(raw):
        if char == marker:
            for char_ in raw[index+1:]:
                if char_.isspace() or char_ == "." or char == "(":
                    break
                name += char_
            break
    
    return name or None

def _get(name, global_ns, local_ns):
    resp = None
    
    if name == PYK_KEYWORDS['PYK_NULL']:
        return PYK_NONE
    
    if local_ns is not None:
        resp = local_ns.get(name)
    
    if resp is None:
        resp = global_ns.get(name)
    
    return resp

async def build_math(raw: str, global_ns, local_ns=None, depth=None):
    args = []
    cur = ""
    for char in raw:

        if char not in ("+", "-", "*", "/"):
            cur += char
            continue

        if not cur:
            raise PYK_SyntaxError("doubled math operators")

        if not args:
            args.append(cur)
            args.append([char])
            cur = ""
            continue

        else:
            args[-1].append(cur)
            args.append([char])
            cur = ""
            continue

    if cur:
        args[-1].append(cur)

    out = 0
    ch = {
        "/": lambda a, b: a / b,
        "*": lambda a, b: a * b,
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b
    }
    for index, arg in enumerate(args):
        if index is 0:
            continue
        if len(arg) != 2:
            raise PYK_SyntaxError("something isnt right")
        front = args[index-1] if not isinstance(args[index-1], list) else out
        typ = arg[0]
        back = arg[1]
        if isinstance(front, str):
            front2 = await get_value_from_string(front, global_ns, local_ns, depth)
        else:
            front2 = front

        back = await get_value_from_string(back, global_ns, local_ns, depth)
        r = ch[typ](front2, back)
        if isinstance(r, int):
            if isinstance(front, str): # i really hate this part, maybe make math parsing not so bad later
                out += r
            else:
                out = r

        else:
            if isinstance(out, int):
                out = r
                continue

            out = r

    return out

def get_variable(raw: str, global_ns, local_ns=None, strict=True, marker=None):
    resp = _get(raw.strip(), global_ns, local_ns)
    if resp is not None:
        return resp
    
    name = get_variable_name(raw, marker)
    if name is None:
        if strict:
            raise PYK_NameError("invalid variable name: '{0}'".format(raw))
        else:
            return None
    
    resp = _get(name, global_ns, local_ns)
    
    if resp is None and strict:
        raise PYK_NameError("name '{0}' is not defined".format(name))
    
    return resp

async def get_variable_or_function_value(name: str, global_ns, local_ns, depth):
    if PYK_BRACKETS['PYK_FUNCTIONCALL_IN'] in name:
        resp = await call_function(name, global_ns, local_ns, depth)
    
    else:
        resp = await get_value_from_string(name, global_ns, local_ns, depth)
    
    return resp


async def call_function(line, global_ns, local_ns, depth):
    func = get_variable(line.split(PYK_BRACKETS['PYK_FUNCTIONCALL_IN'])[0], global_ns, local_ns, marker="")
    t = PYK_BRACKETS['PYK_FUNCTIONCALL_IN'] + PYK_BRACKETS['PYK_FUNCTIONCALL_IN'].join(line.split(PYK_BRACKETS['PYK_FUNCTIONCALL_IN'])[1:])
    args = await parse_call_arguments(t, global_ns, local_ns, depth)
    if isinstance(func, functions.PYKFunction):
        resp = await func.Call(*args, depth=depth)
    elif inspect.iscoroutinefunction(func):
        resp = await func(*args)
    elif callable(func):
        resp = func(*args)
    else:
        raise PYK_Error("{0} is not callable".format(func))

    return resp


async def parse_call_arguments(args: str, global_ns, local_ns, depth) -> list:
    raw_code = find_outer_brackets(args, PYK_BRACKETS['PYK_FUNCTIONCALL_IN'], PYK_BRACKETS['PYK_FUNCTIONCALL_OUT'], include_brackets=False)
    
    args = []
    argname = ""
    string = False
    argument_isstring = False
    for index, char in enumerate(raw_code):
        if char.isspace():
            if string:
                argname += char

            continue

        if char == '"':
            if string and (raw_code[index-1] if index is not 0 else "") != "\\":
                string = False
                continue

            elif not string:
                string = True
                argument_isstring = True

                continue
        
        if char == "," and not string:
            if not argname:
                raise PYK_SyntaxError("Invalid comma")

            args.append((argname, argument_isstring))
            argument_isstring = False
            argname = ""
            continue
        
        argname += char

    if string:
        raise PYK_SyntaxError("expected a closing string quote")

    if argname:
        args.append((argname, argument_isstring))

    resp = []
    for arg, isstring in args:
        if isstring:
            resp.append(arg)
            continue

        if PYK_BRACKETS['PYK_FUNCTIONCALL_IN'] in arg:
            resp.append(await call_function(arg, global_ns, local_ns, depth))
        else:
            v = await get_value_from_string(arg, global_ns, local_ns, depth)
            resp.append(v)
    
    return resp


async def PYK_parse_return(line, global_ns, local_ns, depth):
    line = line.strip().replace(PYK_KEYWORDS['PYK_RETURN'], "", 1).strip()
    if not line:
        return PYK_NONE
    
    resp = await get_value_from_string(line, global_ns, local_ns, depth)
    return resp or PYK_NONE


async def compare_conditional(global_ns, local_ns, depth, arg1, operator=None, arg2=None):
    if not operator and not arg2:
        arg1 = await get_variable_or_function_value(arg1, global_ns, local_ns, depth)
        return bool(arg1)
    
    if operator and not arg2:
        raise PYK_SyntaxError("invalid conditional (operator with no second argument)")
    
    arg1 = await get_variable_or_function_value(arg1, global_ns, local_ns, depth)
    arg2 = await get_variable_or_function_value(arg2, global_ns, local_ns, depth)
    
    if operator in PYK_KEYWORDS['PYK_EQUALS']:
        return arg1 == arg2
    
    if operator in PYK_KEYWORDS['PYK_NOT_EQUALS']:
        return arg1 != arg2
    
    if operator == PYK_KEYWORDS['PYK_GREATER']:
        return arg1 > arg2
    
    if operator == PYK_KEYWORDS['PYK_SMALLER']:
        return arg1 < arg2
    
    if operator == PYK_KEYWORDS['PYK_CONTAINS']:
        return arg1 in arg2
    
    raise PYK_ExecutionError("unknown operator")
    

async def parse_conditional(raw, global_ns, local_ns, depth):
    tests = find_outer_brackets(raw, PYK_BRACKETS['PYK_CONDITIONAL_IN'], PYK_BRACKETS['PYK_CONDITIONAL_OUT'], skip_extra=True, include_brackets=False)
    
    tests = tests.split()
    if len(tests) == 3 or len(tests) == 1:
        return await compare_conditional(global_ns, local_ns, depth, *tests)
    
    else:
        raise PYK_SyntaxError("Invalid conditional (unknown number of conditionals, check there are not spaces in function calls)")


async def _build_line(raw_code, line, lineno, global_ns, local_ns, local, file, skipto, depth):
    if skipto is not None:
        if isinstance(skipto, int):
            if lineno < skipto:
                return skipto
            else:
                local['skipto'] = None
        else:
            if line.strip() == skipto.strip():
                local['skipto'] = None
            else:
                return
    
    line = line.strip()
    if line.startswith(PYK_KEYWORDS['PYK_COMMENT']) or not line:
        return
    
    static = False
    if line.startswith(PYK_KEYWORDS['PYK_STATIC']):
        static = True
        line = line.replace(PYK_KEYWORDS['PYK_STATIC'], "", 1).strip()
    
    if line.startswith(PYK_KEYWORDS['PYK_FUNC']):
        if local_ns is not None:
            raise PYK_SyntaxError("Nested functions are not allowed")
        
        code = line.join(raw_code.split(line)[1:])
        code = line + code
        
        func = functions.PYKFunction(code, file, global_ns)
        global_ns[func.name] = func, static
        return lineno + len(func.code.splitlines())

    if line.startswith(PYK_KEYWORDS['PYK_VARMARKER']):
        name = get_variable_name(line)
        if name is None:
            raise PYK_SyntaxError("invalid variable name")

        getter = line.split("=")

        if len(getter) < 2:
            raise PYK_SyntaxError("declaring variable must have an assignment")

        if PYK_BRACKETS['PYK_FUNCTIONCALL_IN'] in line:
            value = await call_function(line, global_ns, local_ns, depth)
        
        else:
            value = await get_value_from_string(getter[1], global_ns, local_ns, depth)
        
        if local_ns is not None:
            local_ns[name] = value, static
        
        else:
            global_ns[name] = value, static
        
        return
    
    if line.startswith(PYK_KEYWORDS['PYK_RETURN']):
        if local_ns is None:
            raise PYK_SyntaxError("return outside of function")
        
        resp = PYK_parse_return(line, global_ns, local_ns, depth)
        err = StopIteration(resp)
        raise err
    
    if line.startswith(PYK_KEYWORDS['PYK_IF']):
        c = "\n".join(raw_code.splitlines()[lineno:])
        conditional_code = find_outer_brackets(c, skip_extra=True, include_brackets=False)
        _cond = find_outer_brackets(c, skip_extra=True)
        length = len(_cond.splitlines())
        #if line.endswith(PYK_BRACKETS['PYK_CODE_IN']):
        #    length -= 1
        
        found_one = False
        if await parse_conditional(line, global_ns, local_ns, depth):
            found_one = True
            maybe_resp = await build_code_async(conditional_code, global_ns, local_ns, file=file, depth=depth)
            if maybe_resp is not None:
                raise StopIteration(maybe_resp)
        
        
        if line.endswith(PYK_BRACKETS['PYK_CODE_IN']):
            c = c.replace(line.rstrip(PYK_BRACKETS['PYK_CODE_IN']), "", 1)
        else:
            c = c.replace(line + "\n", "", 1)
        c = c.replace(_cond, "", 1).strip()
        
        while c.startswith(PYK_KEYWORDS['PYK_ELIF']):
            conditional_code = find_outer_brackets(c, skip_extra=True, include_brackets=False)
            _cond = find_outer_brackets(c, skip_extra=True)
            length += len(_cond.splitlines())
            
            if not found_one and parse_conditional(c.splitlines()[0], global_ns, local_ns, depth):
                found_one = True
                maybe_resp = await build_code_async(conditional_code, global_ns, local_ns, file=file, depth=depth)
                if maybe_resp is not None:
                    raise StopIteration(maybe_resp)
            
            ln = c.splitlines()[0]
            if ln.endswith(PYK_BRACKETS['PYK_CODE_IN']):
                c = c.replace(ln.rstrip(PYK_BRACKETS['PYK_CODE_IN']), "", 1)
            else:
                c = c.replace(ln + "\n", "", 1)
            c = c.replace(_cond, "", 1).strip()
        
        if c.startswith(PYK_KEYWORDS['PYK_ELSE']):
            conditional_code = find_outer_brackets(c, skip_extra=True, include_brackets=False)
            _cond = find_outer_brackets(c, skip_extra=True)
            length += len(_cond.splitlines())
            if not found_one:
                maybe_resp = await build_code_async(conditional_code, global_ns, local_ns, file=file, depth=depth)
                if maybe_resp is not None:
                    raise StopIteration(maybe_resp)
        
        return length + lineno
    
    if PYK_BRACKETS['PYK_FUNCTIONCALL_IN'] in line:
        await call_function(line, global_ns, local_ns, depth)
        return
    
    raise PYK_SyntaxError("something isnt right: {0}".format(line))

async def build_code_async(raw_code: str, global_namespace, local_namespace=None, file="<input>", depth=0):
    """
    allows for auto-awaiting of async functions
    :param raw_code: the code to evaluate
    :param global_namespace: the global PYK_Namespace
    :param local_namespace: the local PYK_Namespace, if in a function context
    :param file: the file we are currently in
    :param depth: the parse depth, used to prevent python recursionerrors
    :return: Optional[Any]
    """
    if depth >= 100:
        raise PYK_RecursionError("max depth while parsing PYK")  # cutting it close to pythons default recursion depth

    lines = raw_code.splitlines()
    skipto = None

    for index, line in enumerate(lines):
        try:
            r = await _build_line(raw_code, line, index, global_namespace, local_namespace, locals(), file, skipto, depth)
            if r is not None:
                skipto = r
        except StopIteration as e:
            return e.args[0]

        except PYK_Error as error:
            if isinstance(error, PYK_ExecutionError):
                error.file = file
                error.lineno = index
                error.line = line

            raise
