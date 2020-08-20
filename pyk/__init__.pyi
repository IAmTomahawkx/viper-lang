from typing import Optional, Any

from .parser import build_code_async
from .objects import *
from .builtins import get_builtins
from .errors import *
from .common import *

async def eval(raw_code: str, defaults: dict = None, namespace: PYKNamespace = None, file: str = "<string>", safe: bool = False) -> PYKNamespace:
    ...

async def eval_file(fp: str, defaults: dict = None, namespace: PYKNamespace = None, safe: bool = False) -> PYKNamespace:
    ...