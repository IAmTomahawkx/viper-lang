from typing import *
from contextlib import contextmanager

from sly.lex import Lexer, Token

from .scope import Scope, InitialScope
from .lexer import ViperLexer
from .parser import ViperParser
from .ast import *

_quick_exec = (
    Assignment,
    FunctionCall,
    If
)

class Runtime:
    def __init__(self, file: str = "<string>"):
        self.scopes: List[Scope] = []
        self.raw_code = None
        self.file = file
        self.modules = {}
        self.ast = None
        self.null = objects.NULL(self)

    def tokenize(self, source: str, lex: Lexer=ViperLexer()) -> List[Token]:
        """
        tokenizes the source of a viper runtime
        :param source: the source code
        :param lex: An optional lexer to use instead of the ViperLexer. Only recommended if you know what youre doing.
        :return: List[Token]
        """
        self.raw_code = source
        return lex.tokenize(source)

    def parse(self, tokens: List[Token], parser=ViperParser()) -> List[ASTBase]:
        """
        turns the tokens provided by :ref:`~tokenize` into an Abstract Syntax Tree
        :param tokens: the Tokens provided by :ref:`~tokenize`
        :param parser: an optional parser to use instead of ViperParser. Only recommended if you know what youre doing.
        :return: List[ASTBase]
        """
        self.ast = parser.parse(tokens)
        return self.ast

    async def execute(self, ast: List[ASTBase] = None):
        ast = ast or self.ast
        if self.scopes:
            raise RuntimeError("Runtime is already running!")

        with self.new_scope(cls=InitialScope):
            await self.set_variable(Identifier("null", -1, -1), self.null, True)
            await self._common_execute(ast, False)

    async def run(self, source, *, initial_variables: dict = None):
        tokens = [x for x in self.tokenize(source)]
        ast = self.parse(tokens)
        await self.execute(ast)

    @contextmanager
    def new_scope(self, cls=Scope):
        scope = cls(self)
        self.scopes.append(scope)

        try:
            yield scope
        except:
            raise
        else:
            s = self.scopes.pop()
            if s != scope:
                raise RuntimeError("Popped bad scope")

        return scope

    async def set_variable(self, ident: Identifier, value: Any, static: bool):
        scope = self.scopes[-1]
        if isinstance(value, ASTBase):
            value = await value.execute(self)

        scope.set_variable(self, ident, value, static)

    async def get_variable(self, ident: Identifier) -> Optional[objects.VPObject]:
        scopes = reversed(self.scopes)
        for scope in scopes:
            val = scope.get_variable(self, ident, raise_empty=False)
            if val is not None:
                return val

        raise errors.ViperNameError(self, ident.lineno, f"Variable '{ident.name}' not found")

    async def _run_function_body(self, code: List[ASTBase]) -> Any:
        return await self._common_execute(code, True)

    async def _common_execute(self, code: List[ASTBase], in_function=False) -> Any:
        for block in code:
            if type(block) in _quick_exec:
                await block.execute(self)

            elif isinstance(block, Function):
                await self.set_variable(block.name, objects.Function(block, self), block.static)

            else:
                raise ValueError(block)