from typing import *
from contextlib import contextmanager

from sly.lex import Lexer, Token

from .scope import Scope, InitialScope
from .lexer import ViperLexer
from .parser import ViperParser
from .ast import *
from . import lib

_quick_exec = (
    Assignment,
    FunctionCall,
    If,
    Import,
    Try,
    Throw
)

class Runtime:
    def __init__(self, file: str = "<string>", injected: dict = None, *, allow_unsafe_imports: bool = False):
        self.scopes: List[Scope] = []
        injected = injected or {}
        self._injected = injected
        self.raw_code = None
        self.file = file
        self.modules = {}
        self.null = objects.NULL(self)
        self.allow_unsafe_imports = allow_unsafe_imports
        self.session = None

    @property
    def scope(self):
        return self.scopes[-1]

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
        return parser.parse(tokens)

    async def execute(self, ast: List[ASTBase] = None):
        if self.scopes:
            raise RuntimeError("Runtime is already running!")
        injected = {}
        for name, inj in self._injected.items():
            if not isinstance(inj, objects.PyNativeObjectWrapper):
                inj = objects.PyObjectWrapper(self, inj)

            injected[name] = inj

        self._injected = injected

        with self.new_scope(cls=InitialScope, injected=injected):
            await self.set_variable(Identifier("null", -1, -1), self.null, True)
            await self._common_execute(ast)

    async def cleanup(self):
        if self.session:
            await self.session.close()

    async def run(self, source, *, initial_variables: dict = None):
        if initial_variables:
            self._injected.update(initial_variables)

        tokens = [x for x in self.tokenize(source)]
        ast = self.parse(tokens)
        await self.execute(ast)
        await self.cleanup()

    @contextmanager
    def new_scope(self, cls=Scope, injected: dict=None):
        if cls is InitialScope:
            scope = cls(self, injected) # noqa
        else:
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

    async def get_variable(self, ident: Union[Identifier, Attribute]) -> Optional[objects.VPObject]:
        scopes = reversed(self.scopes)
        base_name = ident if isinstance(ident, Identifier) else ident.parent

        for scope in scopes:
            val = scope.get_variable(self, base_name, raise_empty=False)
            if val is not None:
                if isinstance(ident, Attribute):
                    children = [ident.child, *ident.appended_children]
                    for child in children:
                        val = getattr(val, child.name)
                        if not val:
                            raise errors.ViperAttributeError(self, ident.lineno,
                                                             f"Variable '{val}' has no attribute '{child.name}'",
                                                             ident.parent, child)

                return val

        raise errors.ViperNameError(self, ident.lineno, f"Variable '{ident.name}' not found")

    async def _run_function_body(self, code: List[ASTBase]) -> Any:
        return await self._common_execute(code)

    async def _common_execute(self, code: List[ASTBase]) -> Any:
        for block in code:
            if type(block) in _quick_exec:
                await block.execute(self)

            elif isinstance(block, Function):
                try:
                    exists = await self.get_variable(block.name)
                except errors.ViperNameError:
                    exists = None

                if exists and isinstance(exists, objects.Function):
                    exists._ast.matches.append(objects.Function(block, self))
                else:
                    await self.set_variable(block.name, objects.Function(block, self), block.static)

                del exists

            else:
                raise ValueError(block)

    async def import_module(self, name: Identifier, line: int):
        module = lib.import_and_parse(self, line, name.name)
        await self.set_variable(name, module, True)
