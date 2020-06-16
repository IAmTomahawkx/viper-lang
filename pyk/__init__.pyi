from .parser import build_code
from .objects import *
from .builtins import builtins
from .errors import *
from .common import *

def eval(raw_code: str, defaults: dict = None, namespace: PYKNamespace = None, file: str = "<string>") -> PYKNamespace:
    ...

def eval_file(fp: str, defaults: dict = None, namespace: PYKNamespace = None) -> PYKNamespace:
    ...