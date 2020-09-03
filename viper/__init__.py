from .parser import build_code_async
from .objects import *
from .builtins import get_builtins
from .errors import *
from .common import *

__version__ = "0.0.1"

async def eval(raw_code, defaults=None, namespace=None, file="<string>", safe=False):
    """
    :param raw_code: :class:`str` the code to evaluate
    :param defaults: Optional[:class:`dict`] defaults to be statically injected into the namespace before parsing the file
    :param namespace: Optional[:class:`VPNamespace`] a pre-built namespace, useful to keep variables alive between evals
    :param file: :class:`str`
    :param safe: :class:`bool` whether "unsafe" builtins should be used. These include things like file-manipulation parameters.
    :return: :class:`VPNamespace`
    """
    if defaults is not None and not isinstance(defaults, dict):
        raise ValueError("defaults expected a dict")
    
    if namespace is not None and not isinstance(namespace, VPNamespace):
        raise ValueError("namespace expected a VPNamespace")
    
    module_ns = namespace or VPNamespace()
    module_ns.buildmode(True)

    module_ns.update(get_builtins(safe))

    if defaults:
        module_ns.update({a: ((b, True) if not isinstance(b, tuple) else b) for a, b in defaults.items()})
    
    module_ns['globals'] = module_ns
    module_ns.buildmode(False)
    
    await build_code_async(raw_code, module_ns, None, file=file)
    return module_ns

async def eval_file(fp, defaults=None, namespace=None, safe=False):
    """
    :param fp: :class:`str` the file path to read and parse
    :param defaults: Optional[:class`dict`] defaults to be statically injected into the namespace before parsing the file
    :param namespace: Optional[:class:`VPNamespace`] a pre-built namespace, useful to keep variables alive between evals
    :param safe: :class:`bool` whether "unsafe" builtins should be used. These include things like file-manipulation parameters.
    :return: :class:`VPNamespace`
    """
    with open(fp) as f:
        data = f.read()
    
    return await eval(data, defaults, namespace, file=fp, safe=safe)

