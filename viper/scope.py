from typing import *
from . import objects
from .ast import Identifier, ASTBase
from .errors import ViperNameError, ViperStaticError
from .lib._builtins import EXPORTS as _builtin_exports

if TYPE_CHECKING:
    from .runner import Runtime

__all__ = "Scope", "InitialScope"

class Scope:
    def __init__(self, runtime: "Runtime"):
        self._vars = {}
        self._runtime = runtime

    def set_variable(self, runner: "Runtime", item: Identifier, value: objects.VPObject, static: bool, *, force=False):
        if item in self._vars:
            if self._vars[item.name][0] and not force:
                raise ViperStaticError(runner, item.lineno, f"Variable '{item.name}' is static, and cannot be changed.")

        self._vars[item.name] = (value, static)

    def get_variable(self, runner: "Runtime", item: Identifier, *, raise_empty=True):
        if item.name in self._vars:
            return self._vars[item.name][0]

        if raise_empty:
            raise ViperNameError(runner, item.lineno, f"Variable '{item.name}' not found")
        return None

    def del_variable(self, runner: "Runtime", item: Identifier, *, raise_empty=True):
        if item.name in self._vars:
            del self._vars[item.name]
            return

        if raise_empty:
            raise ViperNameError(runner, item.lineno, f"Variable '{item.name}' not found")
        return None

class InitialScope(Scope):
    def __init__(self, runtime: "Runtime", injected: dict):
        super().__init__(runtime)
        for name, value in _builtin_exports.items():
            self._vars[name] = value, True

        for name, value in injected.items():
            self._vars[name] = value, True