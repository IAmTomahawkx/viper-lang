import os

from .parser import build_code
from .objects import *
from .builtins import builtins
from .errors import *
from .common import *

def eval(raw_code, defaults=None, namespace=None, file="<string>"):
    if defaults is not None and not isinstance(defaults, dict):
        raise ValueError("defaults expected a dict")
    
    if namespace is not None and not isinstance(namespace, PYKNamespace):
        raise ValueError("namespace expected a PYKNamespace")
    
    module_ns = namespace or PYKNamespace()
    module_ns.buildmode(True)
    module_ns.update(builtins)
    if defaults:
        module_ns.update(defaults)
    
    module_ns['namespace'] = module_ns
    module_ns.buildmode(False)
    
    build_code(raw_code, module_ns, None)
    return module_ns

def parse_file(fp, defaults=None, namespace=None):
    with open(fp) as f:
        data = f.read()
    
    return eval(data, defaults, namespace, file=fp)

