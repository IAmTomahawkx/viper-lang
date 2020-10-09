import re
from typing import *
from .ast import *
from .options import *
from .errors import *

__all__ = (
    "compile_ast",
    "split_lines"
)

def compile_ast(src: str, filename: str, configuration: Configuration = Configuration()) -> Tree:
    """
    compiles a source string into viper AST.
    :param src: the source string
    :type src: str
    :param filename: the name of the source
    :type filename: str
    :param configuration: the :class:`Configuration` to be used in parsing
    :type configuration: Configuration
    :return: :class:`Tree`
    """
    tree: Tree = Tree(configuration, filename, src)

    lines = split_lines(src, tree)

    ast = []
    current_chain = None

    for line in lines:
        print(line)
        if isinstance(line, LineHolder):
            compiled = _compile_line(line, tree)
        else:
            compiled = _compile_block(line, tree)

        if current_chain and isinstance(compiled, ElseIf):
            current_chain.elif_.append(compiled)
            continue

        elif current_chain and isinstance(compiled, Else):
            current_chain.else_ = compiled
            ast.append(current_chain)
            current_chain = None
            continue

        elif not current_chain and isinstance(compiled, (ElseIf, Else)):
            raise VP_SyntaxError(tree, line.lineno,
                                 "Invalid position for an {0}".format(compiled.__class__.__name__))

        elif current_chain:
            ast.append(current_chain)
            current_chain = None

        if isinstance(compiled, If):
            current_chain = compiled

        else:
            ast.append(compiled)

    print(ast)
    tree.parsed = ast

    return tree

def _compile_line(line: LineHolder, tree: Tree, is_expression: bool = False) -> Optional[Union[AST, List[AST]]]:
    src = line.line
    maybe_constant = re.match(rf"(\"[^\"=]*\")?([0-9])?({tree.configuration.keyword_true}|{tree.configuration.keyword_false})?", src)
    if maybe_constant:
        matches = maybe_constant.groups()
        if matches[0]:
            return String(line.lineno, matches[0].strip('"'))

        elif matches[1]:
            return Int(line.lineno, int(matches[1]))

        elif matches[2]:
            return Bool(line.lineno, matches[2] == tree.configuration.keyword_true)

        del matches

    del maybe_constant

    def _parse_ifelseif(_expr):
        _expr = _expr.strip(tree.configuration.bracket_args_in + tree.configuration.bracket_args_out)
        _expr = _compile_line(LineHolder(line.lineno, _expr), tree, is_expression=True)

        return BoolOp(line.lineno, _expr, None)

    maybe_elif = re.match(fr"{tree.configuration.keyword_elseif} *(.*)", src) # checks for else if (expression)
    if maybe_elif:
        expr = maybe_elif.group(1).strip()
        if expr:
            return ElseIf(line.lineno, _parse_ifelseif(expr), [])

    maybe_if = re.match(fr"{tree.configuration.keyword_if} (.*)", src) # checks for if (expression)
    if maybe_if:
        expr = maybe_if.group(1).strip()
        if expr:
            return If(line.lineno, _parse_ifelseif(expr), [], [], None)

        del expr

    del maybe_if

    if src == tree.configuration.keyword_else:
        return Else(line.lineno, [])

    maybe_assignment = re.match("(static)?([^\n=]*)=(.*)", src)  # checks for `(static) (name) = (expression)`
    if maybe_assignment:
        static, left, right = maybe_assignment.groups()
        if left and right:
            # this is an assignment
            if is_expression:
                raise VP_SyntaxError(tree, line.lineno, "Must be an expression")

            left, right = left.strip(), right.strip()

            if not left.startswith(tree.configuration.reference_marker):
                raise VP_SyntaxError(tree, line.lineno, "Variable name must start with a reference marker ({0})".format(
                    tree.configuration.reference_marker))

            static = static is not None
            name = left.replace(tree.configuration.reference_marker, "", 1)

            return Assignment(line.lineno, static, name,
                              _compile_line(LineHolder(line.lineno, right), tree, is_expression=True))

        del static, left, right

    del maybe_assignment

    maybe_crossassignment = re.match(r"([^\n=]*)([+\-*/])=(.*)", src)  # check for `(name) [+-*/]= (expression)`
    if maybe_crossassignment:
        left, operator, right = maybe_crossassignment.groups()
        left, right = left.strip(), right.strip()

        if left and right and operator:
            if is_expression:
                raise VP_SyntaxError(tree, line.lineno, "Must be an expression")

            if not left.startswith(tree.configuration.reference_marker):
                raise VP_SyntaxError(tree, line.lineno, "Variable name must start with a reference marker ({0})".format(
                    tree.configuration.reference_marker))

            left = left.replace(tree.configuration.reference_marker, "", 1)
            types = {
                "+": PlusEquals,
                "-": MinusEquals,
                "*": TimesEquals,
                "/": DivEquals
            }
            operator = types[operator]
            del types
            ast = operator(line.lineno, left, _compile_line(LineHolder(line.lineno, right), tree))
            return ast

        del left, right, operator

    del maybe_crossassignment

    maybe_func = re.match(fr"({tree.configuration.keyword_static})? ?{tree.configuration.keyword_func} ([a-zA-Z0-9]*) *\{tree.configuration.bracket_args_in}([^)]*)\{tree.configuration.bracket_args_out}", src) # noqa
    if maybe_func:
        name, args = maybe_func.group(1, 2)
        args = args.split(",")
        return Function(line.lineno, "", [Argument(line.lineno, x.replace("?", ""), x.startswith("?")) for x in args])

    # grab anything the regexes dont catch

    items = src.split()
    if len(items) == 1 and tree.configuration.reference_marker in items[0]:
        return Reference(line.lineno, src.replace(tree.configuration.reference_marker, "", 1))

    values = [
        [tree.configuration.keyword_equals, Equals],
        [tree.configuration.keyword_not_equals, NotEquals],
        [tree.configuration.keyword_not_equals, NotEquals],
        [tree.configuration.keyword_not_contains, NotContains],
        [tree.configuration.keyword_contains, Contains],
        [tree.configuration.keyword_smaller, Lesser],
        [tree.configuration.keyword_greater, Greater],
    ]

    def _compile_lr(left, right):
        return _compile_line(LineHolder(line.lineno, left), tree), _compile_line(LineHolder(line.lineno, right), tree)

    try:
        for index, item in enumerate(items):
            nxt = items[index+1]
            for types, response in values:
                if nxt in types:
                    r = " ".join(items[index+2:])
                    if r:
                        left, right = _compile_lr(item, r)
                    else:
                        left, right = _compile_line(LineHolder(line.lineno, item), tree), None
                    return response(line.lineno, left, right)
    except IndexError:
        pass

    raise VP_SyntaxError(tree, line.lineno, "Unexpected token: {0}".format(src.split()[0]))

def _compile_block(block: BlockHolder, tree: Tree) -> AST:
    try:
        caller = _compile_line(LineHolder(block.lineno, block.definer), tree)
    except IndexError:
        caller = None

    inner = split_lines(block.block, tree, line_offset=block.lineno)
    _inner = []
    current_if = None

    for line in inner:
        if isinstance(line, LineHolder):
            if not line.line:
                continue

            compiled = _compile_line(line, tree)
            if current_if and isinstance(compiled, ElseIf):
                current_if.elif_.append(compiled)
                continue

            elif current_if and isinstance(compiled, Else):
                current_if.else_ = compiled
                _inner.append(current_if)
                current_if = None
                continue

            elif not current_if and isinstance(compiled, (ElseIf, Else)):
                raise VP_SyntaxError(tree, line.lineno, "Invalid position for an {0}".format(compiled.__class__.__name__))

            elif current_if:
                _inner.append(current_if)
                current_if = None

            if isinstance(compiled, If):
                current_if = compiled

            else:
                _inner.append(compiled)

        else:
            _inner.append(_compile_block(line, tree))

    if isinstance(caller, (If, ElseIf, Else, Function)):
        caller.code = _inner
        return caller

    raise ValueError(caller)

def split_lines(src: str, tree: Tree, line_offset: int = 0) -> List[Union[LineHolder, BlockHolder]]:
    _src: List[str] = src.splitlines()
    __src: List[str] = []
    for line in _src:
        __src.append(line.strip()) # remove indents and extra whitespace

    src = "\n".join(__src)
    del _src, __src

    resp: List[Union[LineHolder, BlockHolder]] = []

    block = ""
    blocked: Optional[Union[LineHolder, BlockHolder]] = None
    line_no = 1 + line_offset
    in_count = 0

    for index, char in enumerate(src):
        if char == "\n":
            if src[index+1] == tree.configuration.bracket_code_in:
                if not in_count:
                    # the next line is a code_in block, this will need to be a blockHolder
                    blocked = BlockHolder(line_no, block, "")
                    resp.append(blocked)
                    block = ""
                else:
                    # were already in a block
                    blocked.block += char

            elif src[index-1] == tree.configuration.bracket_code_in:
                if in_count < 2:
                    blocked = BlockHolder(line_no, block[0:len(block)-1].strip(), tree.configuration.bracket_code_in)
                    resp.append(blocked)
                    block = ""
                else:
                    blocked.block += char

            else:
                if block and not blocked:
                    blocked = LineHolder(line_no, block)
                    resp.append(blocked)
                    blocked = None
                    block = ""

                elif blocked:
                    blocked.block += char

            line_no += 1
            continue

        if not blocked:
            block += char

        elif isinstance(blocked, LineHolder):
            blocked.line += char

        else:
            blocked.block += char

        if char == tree.configuration.bracket_code_in:
            if not blocked:
                blocked = BlockHolder(line_no, block, char)

            in_count += 1

        elif char == tree.configuration.bracket_code_out:
            in_count -= 1
            if not in_count:
                blocked = None

    return resp

def find_arguments(string: str) -> List[str]:
    in_string = False
    args = [""]

    for index, char in enumerate(string):
        if char == '"':
            args[-1] += char

            if in_string and string[index-1] == "\\":
                args[-1] += char
                continue

            in_string = not in_string
            continue

        if char == "," and not in_string:
            args.append("")
            continue

        args[-1] += char

    return args

def find_outer_brackets(
        tree: Tree,
        lineno: int,
        raw_code: str,
        bracket_in: str = None,
        bracket_out: str = None,
        include_brackets: bool = True,
        skip_extra: bool = False,
        return_excess: bool = False
) -> str:
    """
    returns code up to the outermost bracket
    """
    bracket_in = bracket_in or tree.configuration.bracket_code_in
    bracket_out = bracket_out or tree.configuration.bracket_code_out

    raw_code = raw_code.strip()
    iterator = enumerate(raw_code)
    output = ""
    level = 0

    if not raw_code.startswith(bracket_in):
        if not skip_extra:
            raise VP_SyntaxError(tree, lineno, "Start character, '{0}', not found".format(bracket_in))

        else:
            _, char = next(iterator)
            try:
                while char != bracket_in:
                    if char == "\n":
                        lineno += 1

                    _, char = next(iterator)

                if include_brackets:
                    output += bracket_in
                level += 1
            except StopIteration:
                raise VP_SyntaxError(tree, lineno, "Start character, '{0}', not found".format(bracket_in))

    for index, char in iterator:
        if char == "\n":
            lineno += 1

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
                if return_excess:
                    return raw_code[index + 1:]

                return output

        if not include_brackets:
            output += char

    raise VP_SyntaxError(tree, lineno, "End character, '{0}', not found".format(bracket_out))
