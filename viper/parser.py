import copy
from typing import *

from sly.lex import Token

from .ast import *
from . import objects, errors

quickmaths = {
    "EQ": EqualTo,
    "NE": NotEqualTo,
    "GE": GreaterOrEqual,
    "GT": GreaterThan,
    "LE": LessOrEqual,
    "LT": LessThan,
    "IS": EqualTo,
    "NOT": NotEqualTo,
    "PLUS": Plus,
    "MINUS": Minus,
    "MULTIPLY": Times,
    "DIVIDE": Divide,
    "MODULUS": Modulus,
    "CAST": Cast
}

quick_idents = {
    "STRING": objects.String,
    "INTEGER": objects.Integer,
    "DECIMAL": objects.Integer,
    "TRUE": objects.Boolean,
    "FALSE": objects.Boolean
}

def getanyattr(obj, *names):
    for name in names:
        o = getattr(obj, name, ...)
        if o is not ...:
            return o

def tokens_as_string(tokens):
    return " ".join((t.type for t in tokens))

def greedy_consume_tokens(tokens: List[Token], predicate: Callable, per_step=1):
    ret = []
    index = 0
    while True:
        toks = tokens[index:index+per_step]
        if len(toks) != per_step:
            break

        if predicate(*toks):
            ret.append(toks)
            index += per_step
        else:
            break

    return ret

class Parser:
    def __init__(self):
        self.quick_match = getattr(self, "__quick__", None) or {}

    def parse(self, tokens: List[Token]):
        if not tokens:
            raise ValueError("No tokens passed")

        # first, group tokens into blocks
        grouped_tokens = self._group_blocks(tokens)

        consumed = []
        output = []

        for index, token in enumerate(grouped_tokens):
            # consume tokens until EOL
            if token.type != "EOL":
                consumed.append(token)

            else:
                if not consumed:
                    continue

                ast = self.match(consumed)
                if isinstance(ast, tuple):
                    if ast[1]:
                        raise ValueError(ast)
                    else:
                        ast = ast[0]

                if isinstance(ast, (ElseIf, Else)):
                    if not isinstance(output[-1], If):
                        raise errors.ViperSyntaxError(consumed[0], 0, f"Unexpected {ast.__class__.__name__}")

                    if isinstance(ast, ElseIf):
                        output[-1].others.append(ast)

                    else:
                        if output[-1].finish is not None:
                            raise errors.ViperSyntaxError(consumed[0], 0, "Can only have 1 `else` block")

                        output[-1].finish = ast

                elif isinstance(ast, Catch):
                    if not isinstance(output[-1], Try):
                        raise errors.ViperSyntaxError(consumed[0], 0, f"Unexpected {ast.__class__.__name__}")

                    if output[-1].catch is not None:
                        raise errors.ViperSyntaxError(consumed[0], 0, "Can only have 1 `catch` block")

                    output[-1].catch = ast

                else:
                    output.append(ast)

                consumed.clear()

        if consumed: # match any extras
            ast = self.match(consumed)
            if isinstance(ast, tuple):
                if ast[1]:
                    raise ValueError(ast)
                else:
                    ast = ast[0]

            if isinstance(ast, (ElseIf, Else)):
                if not isinstance(output[-1], If):
                    raise errors.ViperSyntaxError(consumed[0], 0, f"Unexpected {ast.__class__.__name__}")

                if isinstance(ast, ElseIf):
                    output[-1].extras.append(ast)

                else:
                    if output[-1].finish is not None:
                        raise errors.ViperSyntaxError(consumed[0], 0, "Can only have 1 `else` block")

                    output[-1].finish = ast

            elif isinstance(ast, Catch):
                if not isinstance(output[-1], Try):
                    raise errors.ViperSyntaxError(consumed[0], 0, f"Unexpected {ast.__class__.__name__}")

                if output[-1].catch is not None:
                    raise errors.ViperSyntaxError(consumed[0], 0, "Can only have 1 `catch` block")

                output[-1].catch = ast

            else:
                output.append(ast)

            consumed.clear()

        return output


    def _group_blocks(self, tokens: List[Token]) -> List[Union[Block, Token]]:
        output = []
        current_block = None
        depth = 0
        for token in tokens:
            if token.type == "BLOCK_OPEN":
                depth += 1
                if depth == 1:
                    current_block = Block(token.lineno, token.index)
                else:
                    if current_block is not None:
                        current_block.append(token)
                    else:
                        output.append(token)

            elif token.type == "BLOCK_CLOSE":
                depth -= 1
                if depth < 0:
                    raise errors.ViperSyntaxError(token, 0, "Invalid closing bracket")

                if depth == 0:
                    output.append(current_block)
                    current_block = None
                    output.append(dummy(token.lineno, "EOL", token.index + len(token.value)))

                else:
                    if current_block is not None:
                        current_block.append(token)
                    else:
                        output.append(token)

            else:
                if current_block is not None:
                    current_block.append(token)
                else:
                    output.append(token)

        if depth > 0:
            raise errors.ViperSyntaxError(token, "Missing closing bracket") # noqa

        return output

    def match(self, tokens: List[Union[Token, Block]]) -> Optional[ASTBase]:
        pass

    def valid_expr(self, tokens: List[Union[Token, Block]]) -> Optional[Token]:
        """
        returns the first token found that is a statement token.
        If `None` is returned, it is a valid expression
        """
        stmt_tokens = (
            "STATIC",
            "FUNC",
            "IF",
            "ELIF",
            "ELSE",
            "RETURN",
            "EQUALS",
            "TRY",
            "CATCH",
            "THROW"
        )
        for x in tokens:
            if x.type in stmt_tokens:
                return x

        return None

    def _from_token(self, token: Token, offset: int) -> Union[ASTBase, objects.Primary]:
        if token.type in quick_idents:
            return PrimaryWrapper(quick_idents[token.type], token.value, token.lineno, offset)

        if token.type == "IDENTIFIER":
            return Identifier(token.value, token.lineno, offset)

    def _consume_attr(self, it: Iterator, offset: int) -> Tuple[Optional[Attribute], Optional[Token], Iterator]:
        new_it = copy.copy(it) # copy this just in case its a dud
        tok0 = next(new_it)
        if tok0.type != "IDENTIFIER":
            return None, None, it

        tok1 = next(new_it)
        if tok1.type != "ATTR":
            next(it)
            return None, None, it

        tok2 = next(new_it)
        if tok2.type != "IDENTIFIER":
            return None, None, it

        extras = []
        skipped = None
        for tok in new_it:
            if tok.type not in ("IDENTIFIER", "ATTR"):
                skipped = tok
                break

            if tok.type == "IDENTIFIER":
                extras.append(Identifier(tok.value, tok.lineno, offset + tok.index - tok0.index))

        return Attribute(Identifier(tok0.value, tok0.lineno, offset),
                               Identifier(tok2.value, tok2.lineno, offset + tok2.index - tok0.index),
                               tok0.lineno, offset, appended_children=extras), skipped, new_it

    def _parse_cast(self, tokens: List[Token], offset: int) -> Tuple[Cast, List[Token]]:
        if len(tokens) < 3:
            raise errors.ViperSyntaxError(tokens[-1], offset, f"Expected a cast (IDENTIFIER CAST <TYPE>), got {tokens_as_string(tokens)}")

        ident = tokens[0]
        ident = Identifier(ident.value, ident.lineno, offset)
        _c = tokens[1]
        if _c.type != "CAST":
            raise errors.ViperSyntaxError(_c, offset + (_c.index - tokens[0].index), f"Expected a cast, got '{_c.value}'")

        typ = tokens[2]
        if typ.type != "IDENTIFIER":
            raise errors.ViperSyntaxError(typ, offset + (typ.index - tokens[0].index), f"Expected a basic type (string, integer, bool), got '{typ.value}'")

        return Cast(ident, Identifier(typ.value, typ.lineno, offset + (typ.index-tokens[0].index)), ident.lineno, offset), tokens[4:]

    def parse_expr(self, tokens: List[Union[Token, Block]], offset=0, force_valid=False, *, terminator=None) -> Union[ASTBase, objects.Primary]:
        if not force_valid:
            maybe_stmt = self.valid_expr(tokens)
            assert maybe_stmt is None, errors.ViperSyntaxError(maybe_stmt, offset + maybe_stmt.index - tokens[0].index,
                                                               f"Expected a statement, got {maybe_stmt.value}")

        if len(tokens) == 1:
            r = self._from_token(tokens[0], offset) # string, bool, etc
            if r:
                return r
            else:
                return Identifier(tokens[0].value, tokens[0].lineno, offset)

        it = iter(tokens)
        if tokens[0].type == "IDENTIFIER":
            if "CAST" in tokens_as_string(tokens):
                parser, it = self._parse_cast(tokens, offset)
                it = iter(it)
                next_token = next(it, None)

            else:
                attr, skipped, it = self._consume_attr(it, offset)
                if attr is not None:
                    parser = attr
                    try:
                        next_token = next(it) if not skipped else skipped
                    except StopIteration:
                        next_token = None

                else:
                    parser = tokens[0]
                    parser = Identifier(parser.value, parser.lineno, offset)
                    try:
                        next_token = next(it)
                    except StopIteration:
                        next_token = None

        else:
            n = next(it)
            parser = self._from_token(n, offset + n.index - tokens[0].index)
            next_token = next(it)

        if not next_token or next_token.type == terminator:
            return parser

        modifier = quickmaths.get(next_token.type, None)
        r = None
        if not modifier:
            if next_token.type == "PAREN_OPEN":
                # suprise, this is actually a function call
                parser, r = self.match(tokens)
                if not r:
                    return parser
            elif tokens[-1].type == "PAREN_CLOSE":
                tokens.pop(-1)
                return self.parse_expr(tokens, offset, force_valid, terminator=terminator)
            else:
                raise ValueError("wtf", parser, next_token, modifier, tokens)

        if not r:
            r = [x for x in it]

        parsee = self.parse_expr(r, force_valid=True)

        return BiOperatorExpr(parser, modifier, parsee, tokens[0].lineno, offset)

    def _parse_function_args(self, tokens: List[Token], offset: int):
        output = []
        current = []
        start = tokens[0].index
        parsing_default = False

        for index, token in enumerate(tokens):
            if token.type == "COMMA":
                if not current:
                    raise errors.ViperSyntaxError(token, offset + (token.index - start), "Unexpected ','")

                if len(current) == 3:
                    current.append(None) # the default

                if len(current) != 4:
                    raise errors.ViperSyntaxError(token, offset + token.index - start - 1, "Invalid argument")

                output.append(Argument(current[2], current[1], len(output), token.lineno, current[0], current[3]))
                current.clear()
                parsing_default = False
                continue

            if not current:
                current.append(offset + (token.index - start))
                current.append(token.type == "QMARK")

            elif token.type == "QMARK":
                raise errors.ViperSyntaxError(token, offset + (token.index - start), "Unexpected '?'")

            if token.type == "IDENTIFIER" and len(current) == 2:
                current.append(Identifier(token.value, token.lineno, offset + (token.index - start)))
                continue

            if token.type == "EQUALS":
                parsing_default = True
                continue

            if token.type == "IDENTIFIER" and not parsing_default:
                raise errors.ViperSyntaxError(token, offset + token.index - start, f"Unexpected '{token.value}'")

            elif token.type == "IDENTIFIER":
                current.append(self._from_token(token, offset + token.index - start))

            elif token.type == "PAREN_CLOSE":
                if len(current) == 2:
                    current.clear()
                    break

                elif len(current) == 3:
                    current.append(None)  # the default

                if len(current) != 4:
                    raise errors.ViperSyntaxError(current[2], current[0], "Invalid argument")

                output.append(Argument(current[2], current[1], len(output), token.lineno,
                                       current[0]))
                current.clear()
                break

            if token.type != "QMARK":
                raise ValueError("something wrong", token)

        return output

    def parse_function_call_args(self, tokens: List[Token], offset: int) -> Tuple[List[CallArgument], Optional[List[Token]]]:
        output = []
        current = []
        start = tokens[0].index
        depth = 0
        index = 0
        if tokens[0].type != "PAREN_OPEN":
            depth = 1

        math_left = None
        math_opr = None

        for index, token in enumerate(tokens):
            if token.type == "COMMA":
                if not current:
                    raise errors.ViperSyntaxError(token, offset + (token.index - start), "Unexpected ','")

                if math_left:
                    left = self.parse_expr(math_left, math_left[0].index-start)
                    right = self.parse_expr(current, current[0].index-start)
                    output.append(
                        CallArgument(len(output), BiOperatorExpr(left, math_opr, right, left.lineno, left.offset),
                                     token.lineno, left.offset))
                    math_left = None
                    math_opr = None
                else:
                    output.append(
                        CallArgument(len(output), self.parse_expr(current, current[0].index - start), token.lineno,
                                     current[0].index - start))

                current.clear()
                continue

            elif (depth > 1 and token.type not in ("PAREN_OPEN", "PAREN_CLOSE")) or token.type in ("IDENTIFIER", "ATTR", "STRING", "DECIMAL"):
                current.append(token)
                continue

            elif token.type in quickmaths:
                if not current:
                    errors.ViperSyntaxError(token, offset + (token.index - start), f"Unexpected '{token.value}'")

                math_left = current
                math_opr = quickmaths[token.type]
                current = []
                continue

            elif token.type == "PAREN_OPEN":
                depth += 1
                current.append(token)
                continue

            elif token.type == "PAREN_CLOSE":
                depth -= 1
                if depth <= 0:
                    if current:
                        if math_left:
                            left = self.parse_expr(math_left, math_left[0].index - start)
                            right = self.parse_expr(current, current[0].index - start)
                            output.append(
                                CallArgument(len(output),
                                             BiOperatorExpr(left, math_opr, right, left.lineno, left.offset),
                                             token.lineno, left.offset))
                            math_left = None
                            math_opr = None
                        else:
                            output.append(
                                CallArgument(len(output), self.parse_expr(current, current[0].index - start), token.lineno,
                                             current[0].index - start))

                        current.clear()
                    break
                else:
                    current.append(token)
                    continue

            raise ValueError("something wrong", token, token.type)

        if current:
            if math_left:
                raise ValueError
            # can happen when the paren_close gets sheared off of by nested function calls
            output.append(
                CallArgument(len(output), self.parse_expr(current, current[0].index - start), current[0].lineno,
                             current[0].index - start))
        if index != len(tokens):
            remaining = tokens[index+1:]
        else:
            remaining = None

        return output, remaining

    @classmethod
    def quickmatch(cls, pattern: str):
        if not hasattr(cls, "__quick__"):
            cls.__quick__ = {}

        if pattern in cls.__quick__:
            raise ValueError("Quick path already exists")

        def _inner(func):
            cls.__quick__[pattern] = func
            return func

        return _inner

class ViperParser(Parser):
    def match(self, tokens):
        # first, check the quickmatches
        stringed = tokens_as_string(tokens)
        for q, func in self.quick_match.items():
            if stringed.startswith(q):
                # we've got a hit
                return func(self, tokens)

        if "PAREN_OPEN" in stringed and (stringed.startswith("IDENTIFIER")):
            return self.expr_func_call(tokens)

        raise errors.ViperSyntaxError(tokens[0], 0, "Invalid Syntax")

    @Parser.quickmatch("IMPORT")
    def stmt_imprt(self, tokens):
        imprt = tokens[0]
        del tokens[0]

        if not tokens:
            raise errors.ViperSyntaxError(imprt, 0, "Expected a module, got nothing")

        module = tokens[0]
        if module.type != "IDENTIFIER":
            raise errors.ViperSyntaxError(module, module.index - imprt.index, f"Expected a module name, got {module.value}")

        return Import(Identifier(module.value, module.lineno, module.index - imprt.index), module.lineno, 0)

    @Parser.quickmatch("TRY")
    def stmt_try(self, tokens):
        assert len(tokens) == 2 and isinstance(tokens[1], Block)
        return Try(self.parse(tokens[1]), tokens[0].lineno, 0)

    @Parser.quickmatch("THROW")
    def stmt_throw(self, tokens):
        expr = self.parse_expr(tokens[1:], tokens[1].index - tokens[0].index)
        return Throw(expr, tokens[0].lineno, 0)

    @Parser.quickmatch("CATCH")
    def stmt_catch(self, tokens):
        assert len(tokens) == 2 and isinstance(tokens[1], Block)
        return Catch(self.parse(tokens[1]), tokens[0].lineno, 0)

    @Parser.quickmatch("FUNC")
    @Parser.quickmatch("STATIC FUNC")
    def stmt_func(self, tokens):
        line_start = tokens[0].index
        static = tokens[0].type == "STATIC"

        if static:
            name = Identifier(tokens[2].value, tokens[2].lineno, tokens[2].index - line_start)
            args = self._parse_function_args(tokens[4:], tokens[4].index - line_start)
        else:
            name = Identifier(tokens[1].value, tokens[1].lineno, tokens[1].index - line_start)
            args = self._parse_function_args(tokens[3:], tokens[3].index - line_start)

        return Function(name, self.parse(tokens[-1]), args, static, tokens[0].lineno, 0)

    @Parser.quickmatch("IDENTIFIER ATTR IDENTIFIER")
    def q_expr_attr(self, tokens):
        start = tokens[0].index
        it = iter(tokens)
        missed = None

        children = []

        for tok in it:
            if tok.type not in ("IDENTIFIER", "ATTR"):
                missed = tok
                break

            if tok.type == "ATTR":
                continue

            if tok.type == "IDENTIFIER":
                children.append(tok)

        attr = Attribute(
                        Identifier(children[0].value, children[0].lineno, children[0].index - start),
                        Identifier(children[1].value, children[1].lineno, children[1].index - start),
                        children[0].lineno,
                        0,
                        [Identifier(x.value, x.lineno, x.index - start) for x in children[2:]])

        if missed:
            rest = [missed, *it]
        else:
            # nothing was missed, we probably hit the end of the tokens, so return what we have
            return attr

        if rest[0].type == "PAREN_OPEN": # function call
            # dont pass the opening bracket
            del rest[0]
            return self.common_expr_func_call(attr, rest, rest[0].index-start)
        else:
            raise ValueError(attr, rest)


    @Parser.quickmatch("IDENTIFIER PAREN_OPEN")
    def q_expr_func_call(self, tokens):
        name = tokens[0]
        name = Identifier(name.value, name.lineno, 0)
        return self.common_expr_func_call(name, tokens[2:], tokens[2].index - tokens[0].index)

    def expr_func_call(self, tokens):
        value = []
        start = tokens[0].index
        it = iter(tokens)
        missed = None

        for tok in it:
            if tok.type not in ("IDENTIFIER", "ATTR"):
                if tok.type != "PAREN_IN":
                    missed = tok
                break

            if tok.type == "IDENTIFIER":
                value.append(Identifier(tok.value, tok.lineno, tok.index - start))

        if len(value) > 1:
            name = Attribute(value[0], value[1], tokens[0].lineno, 0, appended_children=value[2:])
            vals = [missed, *(x for x in it)] if missed else [x for x in it]
        else:
            name = Identifier(value[0].name, value[0].lineno, value[0].offset - start)
            vals = [missed, *(x for x in it)] if missed else [x for x in it]

        return self.common_expr_func_call(name, vals, vals[0].index - start)


    def common_expr_func_call(self, name: Union[Identifier, Attribute], tokens, offset: int):
        args, remaining = self.parse_function_call_args(tokens, offset)

        return FunctionCall(name, args, tokens[0].lineno, offset), remaining

    def stmt_ifelseif_parse(self, tokens):
        it = iter(tokens)
        next(it)  # drop the identity
        pin = next(it)
        if pin.type != "PAREN_OPEN":
            raise errors.ViperSyntaxError(pin, pin.index - tokens[0].index, f"Expected '(', got '{pin.value}'")

        args = []
        for x in it:
            if x.type == "PAREN_CLOSE":
                args.append(x)
                break

            args.append(x)

        values = self.parse_function_call_args(args, pin.index - tokens[0].index)[0]
        # turns out function argument parsing is almost identical to this, with the exception that this needs exactly
        # one argument, and it needs some sort of equality check. its pretty easy to extract the value from the returned
        # CallArgument, so this provides a convenient method to parse the value

        if not values:
            raise errors.ViperSyntaxError(pin, pin.index - tokens[0].index, "Expected a condition, got nothing")

        if len(values) > 1:
            raise errors.ViperSyntaxError(pin, pin.index - tokens[0].index, "Too many expressions for an if statement.")

        values = values[0]
        values = values.value
        if not isinstance(values, BiOperatorExpr):
            raise errors.ViperSyntaxError(pin, pin.index - tokens[0].index,
                                          f"Expected a comparison, got <{values.__class__.__name__}>")

        return values

    @Parser.quickmatch("IF")
    def stmt_if_block(self, tokens):
        value = self.stmt_ifelseif_parse(tokens)
        if not isinstance(tokens[-1], list):
            raise errors.ViperSyntaxError(tokens[-1], tokens[-1].index - tokens[0].index, f"Expected a code block, got '{tokens[-1].type}'")

        return If(value, self.parse(tokens[-1]), tokens[0].lineno, 0)

    @Parser.quickmatch("ELIF")
    def stmt_elseif_block(self, tokens):
        value = self.stmt_ifelseif_parse(tokens)
        if not isinstance(tokens[-1], list):
            raise errors.ViperSyntaxError(tokens[-1], tokens[-1].index - tokens[0].index, f"Expected a code block, got '{tokens[-1].type}'")

        return ElseIf(value, self.parse(tokens[-1]), tokens[0].lineno, 0)

    @Parser.quickmatch("ELSE")
    def stmt_else_block(self, tokens):
        if not isinstance(tokens[-1], list):
            raise errors.ViperSyntaxError(tokens[-1], tokens[-1].index - tokens[0].index, f"Expected a code block, got '{tokens[-1].type}'")

        return Else(self.parse(tokens[-1]), tokens[-1].lineno, tokens[-1].index - tokens[0].index)

    # this needed to be moved below the functioncall line, or the quickmatcher would call this instead of function calls
    @Parser.quickmatch("IDENTIFIER")
    @Parser.quickmatch("STATIC IDENTIFIER")
    def stmt_assign(self, tokens):
        line_start = tokens[0].index
        static = tokens[0].type == "STATIC"
        if static:
            name = Identifier(tokens[1].value, tokens[1].lineno, tokens[1].index - line_start)
            expr = self.parse_expr(list(tokens[3:]), tokens[3].index - line_start)
        else:
            name = Identifier(tokens[0].value, tokens[0].lineno, tokens[0].index - line_start)
            expr = self.parse_expr(list(tokens[2:]), tokens[2].index - line_start)

        return Assignment(name, expr, tokens[0].lineno, line_start, static)