from typing import Optional, Any

from .parser import build_code_async
from .objects import *
from .builtins import get_builtins
from .errors import *
from .common import *

async def eval(raw_code: str, defaults: dict = None, namespace: VPNamespace = None, file: str = "<string>", safe: bool = False) -> VPNamespace:
    ...

async def eval_file(fp: str, defaults: dict = None, namespace: VPNamespace = None, safe: bool = False) -> VPNamespace:
    ...