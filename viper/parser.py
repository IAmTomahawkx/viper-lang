import copy
from typing import *
from pprint import pprint

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
        pprint(grouped_tokens, indent=4)

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
                consumed.clear()
                output.append(ast)

        if consumed: # match any extras
            ast = self.match(consumed)
            consumed.clear()
            if isinstance(ast, (ElseIf, Else)):
                if not isinstance(output[-1], If):
                    raise errors.ViperSyntaxError(consumed[0], 0, f"Unexpected {ast.__class__.__name__}")

                if isinstance(ast, ElseIf):
                    output[-1].extras.append(ast)

            else:
                output.append(ast)

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
            "EQUALS"
        )
        for x in tokens:
            if x.type in stmt_tokens:
                return x

        return None

    def _from_token(self, token: Token, offset: int) -> Union[ASTBase, objects.Primary]:
        if token.type in quick_idents:
            return quick_idents[token.type](token.value)

        if token.type == "IDENTIFIER":
            return Identifier(token.value, token.lineno, offset)

    def _consume_attr(self, it: Iterator, offset: int) -> Tuple[Optional[Attribute], Iterator]:
        new_it = copy.copy(it) # copy this just in case its a dud
        tok0 = next(new_it)
        if tok0.type != "IDENTIFIER":
            return None, it

        tok1 = next(new_it)
        if tok1.type != "ATTR":
            next(it)
            return None, it

        tok2 = next(new_it)
        if tok2.type != "IDENTIFIER":
            return None, it

        extras = []
        for tok in new_it:
            if tok.type not in ("IDENTIFIER", "ATTR"):
                break

            if tok.type == "IDENTIFIER":
                extras.append(Identifier(tok.value, tok.lineno, offset + tok.index - tok0.index))

        return Attribute(Identifier(tok0.value, tok0.lineno, offset),
                               Identifier(tok2.value, tok2.lineno, offset + tok2.index - tok0.index),
                               tok0.lineno, offset, appended_children=extras), new_it

    def parse_expr(self, tokens: List[Union[Token, Block]], offset=0, force_valid=False) -> Union[ASTBase, objects.Primary]:
        if not force_valid:
            maybe_stmt = self.valid_expr(tokens)
            assert maybe_stmt is None, errors.ViperSyntaxError(maybe_stmt, offset + maybe_stmt.index - tokens[0].index,
                                                               f"Expected a statement, got {maybe_stmt.value}")

        if len(tokens) == 1:
            return self._from_token(tokens[0], offset) # string, bool, etc

        if len(tokens) == 2:
            return Identifier(tokens[1].value, tokens[1].lineno, (tokens[1].index - tokens[0].index) + offset)

        it = iter(tokens)
        if tokens[0].type == "IDENTIFIER":
            attr, it = self._consume_attr(it, offset)
            if attr is not None:
                parser = attr
                next_token = next(it)

            else:
                parser = tokens[0]
                next_token = next(it)

        else:
            n = next(it)
            parser = self._from_token(n, offset + n.index - tokens[0].index)
            next_token = next(it)

        if not next_token:
            return parser

        modifier = quickmaths.get(next_token.type, None)
        if not modifier:
            raise ValueError("wtf", parser, next_token, modifier)

        r = [x for x in it]
        parsee = self.parse_expr(r, force_valid=True)

        return BiOperatorExpr(parser, modifier, parsee, parser.lineno, offset)

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
                if len(current) == 3:
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

    def parse_function_call_args(self, tokens: List[Token], offset: int) -> List[CallArgument]:
        output = []
        current = []
        start = tokens[0].index

        for index, token in enumerate(tokens):
            if token.type == "COMMA":
                if not current:
                    raise errors.ViperSyntaxError(token, offset + (token.index - start), "Unexpected ','")

                output.append(
                    CallArgument(len(output), self.parse_expr(current, current[0].index - start), token.lineno,
                                 current[0].index - start))
                current.clear()
                continue

            elif token.type in ("IDENTIFIER", "ATTR", *quickmaths):
                current.append(token)
                continue

            elif token.type == "PAREN_CLOSE":
                if current:
                    output.append(
                        CallArgument(len(output), self.parse_expr(current, current[0].index - start), token.lineno,
                                     current[0].index - start))

                    current.clear()
                break

            raise ValueError("something wrong", token)

        return output

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
        print(stringed)
        for q, func in self.quick_match.items():
            if stringed.startswith(q):
                # we've got a hit
                return func(self, tokens)

        if "PAREN_OPEN" in stringed and (stringed.startswith("IDENTIFIER")):
            return self.expr_func_call(tokens)

        raise errors.ViperSyntaxError(tokens[0], 0, "Invalid Syntax")

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

    @Parser.quickmatch("IDENTIFIER PAREN_OPEN")
    def q_expr_func_call(self, tokens):
        name = tokens[0]
        name = Identifier(name.value, name.lineno, 0)
        return self.common_expr_func_call(name, tokens[2:], tokens[2].index - tokens[0].index)

    def expr_func_call(self, tokens):
        value = []
        start = tokens[0].index
        it = iter(tokens)
        for tok in it:
            if tok.type not in ("IDENTIFIER", "ATTR"):
                break

            if tok.type == "IDENTIFIER":
                value.append(Identifier(tok.value, tok.lineno, tok.index - start))

        name = Attribute(value[0], value[1], tokens[0].lineno, 0, appended_children=value[2:])
        vals = [x for x in it]
        return self.common_expr_func_call(name, vals, vals[0].index - start)


    def common_expr_func_call(self, name: Union[Identifier, Attribute], tokens, offset: int):
        start = tokens[0].index
        args = []
        current = []

        for tok in tokens:
            if tok.type == "PAREN_CLOSE":
                args.append(CallArgument(len(args), self.parse_expr(current, offset + (current[0].index - start)),
                                         current[0].lineno, offset + (current[0].index - start)))
                current.clear()
                break

            if tok.type == "COMMA":
                if not current:
                    raise errors.ViperSyntaxError(tok, offset + (tok.index - start), "Unexpected ','")

                args.append(CallArgument(len(args), self.parse_expr(current, offset + (current[0].index - start)),
                                         current[0].lineno, offset + (current[0].index - start)))
                current.clear()
                continue

            current.append(tok)

        return FunctionCall(name, args, tokens[0].lineno, offset)

    def stmt_ifelseif_parse(self, tokens):
        it = iter(tokens)
        next(it)  # drop the identity
        pin = next(it)
        if pin.type != "PAREN_OPEN":
            raise errors.ViperSyntaxError(pin, pin.index - tokens[0].index, f"Expected '(', got '{pin.value}'")

        values = self.parse_function_call_args([x for x in it], pin.index - tokens[0].index)
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
