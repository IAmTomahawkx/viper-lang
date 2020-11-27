from .runner import Runtime
from .scope import Scope, InitialScope
from . import objects
from .objects import String, Integer, Boolean

__version__ = "1.0.0a1"

async def eval(code: str, filename="<string>", injected: dict=None) -> Runtime:
    runtime = Runtime(filename, injected)
    await runtime.run(code)
    return runtime