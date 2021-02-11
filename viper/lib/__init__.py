import importlib
from viper import objects, errors

import typing
if typing.TYPE_CHECKING:
    from ..runner import Runtime

# module: unsafe
MODULES = {
    "regex": False,
    "files": True,
    "requests": True,
    "json": False,
    "random": False
}

def is_importable(module):
    return module in MODULES

def import_and_parse(runner: "Runtime", lineno: int, module: str) -> objects.Module:
    if not is_importable(module):
        raise errors.ViperModuleError(runner, lineno, f"Cannot import '{module}'")

    mod = importlib.import_module(f"viper.lib.{module}")
    mod = objects.Module(module, mod, runner)
    return mod