import inspect

from .keywords import VIPER_BRACKETS, VIPER_STRICT_PARSING_KEYWORDS, VIPER_KEYWORDS
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
                    raise VP_SyntaxError("Invalid escape")
            
            if char == '"':
                if depth:
                    return resp
                depth = True
                continue
            if depth:
                resp += char

        raise VP_SyntaxError("Invalid string")

    
    if raw.startswith(VIPER_KEYWORDS['VIPER_VARMARKER']):
        if VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'] in raw:
            var = await call_function(raw, global_ns, local_ns, depth)
        else:
            var = get_variable(raw, global_ns, local_ns)

        return var
    
    if raw == VIPER_KEYWORDS['VIPER_TRUE']:
        return True
    
    if raw == VIPER_KEYWORDS['VIPER_FALSE']:
        return False
    
    if raw == VIPER_KEYWORDS['VIPER_NULL']:
        return VP_NONE
    
    if not raw.isalpha():
        try:
            return int(raw)
        except ValueError:
            try:
                return float(raw)
            except ValueError:
                pass
    
    if VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'] in raw:
        return await call_function(raw, global_ns, local_ns, depth)
    
    if local_ns is not None:
        var = local_ns.get(raw)
        if var is not None:
            return var
    
    var = global_ns.get(raw)
    if var is not None:
        return var
    
    raise VP_NameError(raw)

def get_variable_name(raw: str, marker=None):
    name = ""
    if raw in [VIPER_KEYWORDS['VIPER_TRUE'], VIPER_KEYWORDS['VIPER_FALSE']]:
        return raw
    
    marker = marker or VIPER_KEYWORDS['VIPER_VARMARKER']
    for index, char in enumerate(raw):
        if char == marker:
            for char_ in raw[index+1:]:
                if char_.isspace() or char == "(":
                    break
                name += char_
            break
    
    return name or None

def _get(name, global_ns, local_ns):
    resp = None
    
    if name == VIPER_KEYWORDS['VIPER_NULL']:
        return VP_NONE


    
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
            raise VP_SyntaxError("doubled math operators")

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
            raise VP_SyntaxError("something isnt right")
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
            raise VP_NameError("invalid variable name: '{0}'".format(raw))
        else:
            return None

    subs = name.split(".")
    if len(subs) > 1:
        cur = [subs[0]]
        resp = _get(subs[0], global_ns, local_ns)
        for attr in subs[1:]:
            cur.append(attr)

            if attr.startswith("_"):
                raise VP_AttributeError("underscored attributes are private, and cannot be accessed. ({0})".format(".".join(cur)))

            try:
                resp = getattr(resp, attr)
            except AttributeError:
                raise VP_AttributeError("{0} has no attribute {1} ({2})".format(resp, attr, ".".join(cur)))

    else:
        resp = _get(name, global_ns, local_ns)
    
    if resp is None and strict:
        raise VP_NameError("name '{0}' is not defined".format(name))
    
    return resp

async def get_variable_or_function_value(name: str, global_ns, local_ns, depth):
    if VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'] in name:
        resp = await call_function(name, global_ns, local_ns, depth)
    
    else:
        resp = await get_value_from_string(name, global_ns, local_ns, depth)
    
    return resp


async def call_function(line, global_ns, local_ns, depth):
    func = get_variable(line.split(VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'])[0].split("=")[-1].strip(), global_ns, local_ns, marker="")
    t = VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'] + VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'].join(line.split(VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'])[1:])
    args = await parse_call_arguments(t, global_ns, local_ns, depth)

    if isinstance(func, functions.VPFunction):
        resp = await func.Call(*args, depth=depth)
    elif inspect.iscoroutinefunction(func):
        resp = await func(*args)
    elif callable(func):
        resp = func(*args)
    else:
        raise VP_Error("{0} is not callable".format(func))

    return resp


async def parse_call_arguments(args: str, global_ns, local_ns, depth) -> list:
    raw_code = find_outer_brackets(args, VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'], VIPER_BRACKETS['VIPER_FUNCTIONCALL_OUT'], include_brackets=False)
    
    args = []
    argname = ""
    string = False
    argument_isstring = False
    bracketed = 0
    for index, char in enumerate(raw_code):
        if char.isspace():
            if string or bracketed > 0:
                argname += char

            continue

        if char == VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'] and not string:
            bracketed += 1

        if char == VIPER_BRACKETS['VIPER_FUNCTIONCALL_OUT'] and not string:
            bracketed -= 1

        if char == '"' and bracketed < 1:
            if string and (raw_code[index-1] if index is not 0 else "") != "\\":
                string = False
                continue

            elif not string:
                string = True
                argument_isstring = True

                continue
        
        if char == "," and not string and bracketed == 0:
            if not argname:
                raise VP_SyntaxError("Invalid comma")

            if argument_isstring:
                argname = '"' + argname + '"'
            args.append(argname)
            argument_isstring = False
            argname = ""
            continue
        
        argname += char

    if string:
        raise VP_SyntaxError("expected a closing string quote")

    if argname:
        if argument_isstring:
            argname = '"' + argname + '"'

        args.append(argname)

    resp = []
    for arg in args:
        v = await get_value_from_string(arg, global_ns, local_ns, depth)
        resp.append(v)
    
    return resp


async def viper_parse_return(line, global_ns, local_ns, depth):
    line = line.strip().replace(VIPER_KEYWORDS['VIPER_RETURN'], "", 1).strip()
    if not line:
        return VP_NONE
    
    resp = await get_value_from_string(line, global_ns, local_ns, depth)
    return resp or VP_NONE


async def compare_conditional(global_ns, local_ns, depth, arg1, operator=None, arg2=None):
    if not operator and not arg2:
        arg1 = await get_variable_or_function_value(arg1, global_ns, local_ns, depth)
        return bool(arg1)
    
    if operator and not arg2:
        raise VP_SyntaxError("invalid conditional (operator with no second argument)")
    
    arg1 = await get_variable_or_function_value(arg1, global_ns, local_ns, depth)
    arg2 = await get_variable_or_function_value(arg2, global_ns, local_ns, depth)
    
    if operator in VIPER_KEYWORDS['VIPER_EQUALS']:
        return arg1 == arg2
    
    if operator in VIPER_KEYWORDS['VIPER_NOT_EQUALS']:
        return arg1 != arg2
    
    if operator == VIPER_KEYWORDS['VIPER_GREATER']:
        return arg1 > arg2
    
    if operator == VIPER_KEYWORDS['VIPER_SMALLER']:
        return arg1 < arg2
    
    if operator == VIPER_KEYWORDS['VIPER_CONTAINS']:
        return arg1 in arg2

    if operator == VIPER_KEYWORDS['VIPER_NOTCONTAINS']:
        return arg1 not in arg2
    
    raise VP_ExecutionError("unknown operator")
    

async def parse_conditional(raw, global_ns, local_ns, depth):
    tests = find_outer_brackets(raw, VIPER_BRACKETS['VIPER_CONDITIONAL_IN'], VIPER_BRACKETS['VIPER_CONDITIONAL_OUT'], skip_extra=True, include_brackets=False)
    
    tests = tests.split()
    if len(tests) == 3 or len(tests) == 1:
        return await compare_conditional(global_ns, local_ns, depth, *tests)
    
    else:
        raise VP_SyntaxError("Invalid conditional (unknown number of conditionals, check there are not spaces in function calls)")

async def _build_line(raw_code, line, lineno, global_ns, local_ns, local, file, skipto, depth, func):
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
    if line.startswith(VIPER_KEYWORDS['VIPER_COMMENT']) or not line:
        return
    
    static = False
    if line.startswith(VIPER_KEYWORDS['VIPER_STATIC']):
        static = True
        line = line.replace(VIPER_KEYWORDS['VIPER_STATIC'], "", 1).strip()
    
    if line.startswith(VIPER_KEYWORDS['VIPER_FUNC']):
        if local_ns is not None:
            raise VP_SyntaxError("Nested functions are not allowed")
        
        code = line.join(raw_code.split(line)[1:])
        code = line + code
        
        func = functions.VPFunction(code, file, global_ns)
        global_ns[func.name] = func, static
        return lineno + len(func.code.splitlines())

    if line.startswith(VIPER_KEYWORDS['VIPER_VARMARKER']):
        name = get_variable_name(line)
        if name is None:
            raise VP_SyntaxError("invalid variable name")

        getter = line.split("=")

        if len(getter) < 2:
            if VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'] in line:
                await call_function(line, global_ns, local_ns, depth)
                return

            raise VP_SyntaxError("declaring variable must have an assignment")

        if VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'] in line:
            value = await call_function(line, global_ns, local_ns, depth)
        
        else:
            value = await get_value_from_string(getter[1], global_ns, local_ns, depth)
        
        if local_ns is not None:
            local_ns[name] = value, static
        
        else:
            global_ns[name] = value, static
        
        return
    
    if line.startswith(VIPER_KEYWORDS['VIPER_RETURN']):
        if local_ns is None:
            raise VP_SyntaxError("return outside of function")
        
        resp = viper_parse_return(line, global_ns, local_ns, depth)
        err = StopIteration(resp)
        raise err

    if line.startswith(VIPER_KEYWORDS['VIPER_THROW']):
        value = await get_value_from_string(line.replace(VIPER_KEYWORDS['VIPER_THROW'], "", 1).strip(), global_ns, local_ns, depth)
        raise VP_RaisedError(repr(value))
    
    if line.startswith(VIPER_KEYWORDS['VIPER_IF']):
        c = "\n".join(raw_code.splitlines()[lineno:])
        conditional_code = find_outer_brackets(c, skip_extra=True, include_brackets=False)
        _cond = find_outer_brackets(c, skip_extra=True)
        excess = find_outer_brackets(c, skip_extra=True, return_excess=True)
        length = len(_cond.splitlines())
        
        found_one = False
        if await parse_conditional(line, global_ns, local_ns, depth):
            found_one = True
            maybe_resp = await build_code_async(conditional_code, global_ns, local_ns, file=file, depth=depth, func=func)
            if maybe_resp is not None:
                raise StopIteration(maybe_resp)
        
        c = excess.strip()

        while c.startswith(VIPER_KEYWORDS['VIPER_ELIF']):
            conditional_code = find_outer_brackets(c, skip_extra=True, include_brackets=False)
            _cond = find_outer_brackets(c, skip_extra=True)
            excess = find_outer_brackets(c, skip_extra=True, return_excess=True)
            length += len(_cond.splitlines())
            
            if not found_one and await parse_conditional(c.splitlines()[0], global_ns, local_ns, depth):
                found_one = True
                maybe_resp = await build_code_async(conditional_code, global_ns, local_ns, file=file, depth=depth, func=func)
                if maybe_resp is not None:
                    raise StopIteration(maybe_resp)

            c = excess.strip()


        if c.startswith(VIPER_KEYWORDS['VIPER_ELSE']):
            v = c.replace(VIPER_KEYWORDS['VIPER_ELSE'], "", 1).strip()
            conditional_code = find_outer_brackets(v, skip_extra=True, include_brackets=False)
            _cond = find_outer_brackets(v, skip_extra=True)
            length += len(_cond.splitlines())

            if not found_one:
                maybe_resp = await build_code_async(conditional_code, global_ns, local_ns, file=file, depth=depth, func=func)
                if maybe_resp is not None:
                    raise StopIteration(maybe_resp)

        return length + lineno

    if line.startswith(VIPER_KEYWORDS['VIPER_TRY']):
        c = "\n".join(raw_code.splitlines()[lineno:])
        maybe_error = find_outer_brackets(c, skip_extra=True, include_brackets=False)
        maybe_error_code = find_outer_brackets(c, skip_extra=True)
        rest = find_outer_brackets(c, skip_extra=True, return_excess=True).strip()
        length = len(maybe_error_code.splitlines())
        find_end = lineno + length
        while not raw_code.splitlines()[find_end].strip():
            find_end += 1

        if not rest.startswith(VIPER_KEYWORDS['VIPER_CATCH']):
            raise VP_SyntaxError(f"\"{VIPER_KEYWORDS['VIPER_TRY']}\" block without a \"{VIPER_KEYWORDS['VIPER_CATCH']}\" statement")

        catch_block = find_outer_brackets(rest, skip_extra=True, include_brackets=False).strip()
        catch_end = len(find_outer_brackets(rest, skip_extra=True, include_brackets=True).splitlines()) + find_end

        try:
            await build_code_async(maybe_error, global_ns, local_ns, file=file, depth=depth, func=func)
        except VP_Error as error:
            if local_ns:
                local_ns.force_assign("error", error, True)
            else:
                global_ns.force_assign("error", error, True)

            await build_code_async(catch_block, global_ns, local_ns, file=file, depth=depth, func=func)

            if local_ns:
                del local_ns['error']

            else:
                del global_ns['error']

        return catch_end

    if VIPER_BRACKETS['VIPER_FUNCTIONCALL_IN'] in line:
        await call_function(line, global_ns, local_ns, depth)
        return
    
    raise VP_SyntaxError("something isnt right: {0}".format(line))

async def build_code_async(raw_code: str, global_namespace, local_namespace=None, file="<input>", depth=0, func=None):
    """
    allows for auto-awaiting of async functions
    :param raw_code: the code to evaluate
    :param global_namespace: the global VP_Namespace
    :param local_namespace: the local VP_Namespace, if in a function context
    :param file: the file we are currently in
    :param depth: the parse depth, used to prevent python recursionerrors
    :param func: the function we are currently in, used to gather stack traces
    :return: Optional[Any]
    """
    if depth >= 100:
        raise VP_RecursionError("max depth while parsing viper")  # cutting it close to pythons default recursion depth

    lines = raw_code.splitlines()
    skipto = None

    for index, line in enumerate(lines):
        if skipto and index <= skipto:
            continue

        skipto = None
        try:
            r = await _build_line(raw_code, line, index, global_namespace, local_namespace, locals(), file, skipto, depth, func)
            if r is not None:
                skipto = r
        except StopIteration as e:
            return e.args[0]

        except VP_Error as error:
            error.file = file
            error.line = line
            error.stack.append((func, line, file))

            raise
