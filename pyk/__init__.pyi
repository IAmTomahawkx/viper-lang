from .parser import build_code
from .objects import *
from .builtins import builtins
from .errors import *
from .common import *

async def eval(raw_code: str, defaults: dict = None, namespace: PYKNamespace = None, file: str = "<string>") -> PYKNamespace:
    ...

async def eval_file(fp: str, defaults: dict = None, namespace: PYKNamespace = None) -> PYKNamespace:
    ...