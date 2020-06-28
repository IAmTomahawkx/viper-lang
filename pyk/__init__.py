from .parser import build_code_async
from .objects import *
from .builtins import builtins
from .errors import *
from .common import *

__version__ = "0.0.1"

async def eval(raw_code, defaults=None, namespace=None, file="<string>"):
    """
    :param raw_code: :class:`str` the code to evaluate
    :param defaults: Optional[:class:`dict`] defaults to be statically injected into the namespace before parsing the file
    :param namespace: Optional[:class:`PYKNamespace`] a pre-built namespace, useful to keep variables alive between evals
    :param file: :class:`str`
    :return: :class:`PYKNamespace`
    """
    if defaults is not None and not isinstance(defaults, dict):
        raise ValueError("defaults expected a dict")
    
    if namespace is not None and not isinstance(namespace, PYKNamespace):
        raise ValueError("namespace expected a PYKNamespace")
    
    module_ns = namespace or PYKNamespace()
    module_ns.buildmode(True)

    module_ns.update(builtins)

    if defaults:
        module_ns.update({a: ((b, True) if not isinstance(b, tuple) else b) for a, b in defaults.items()})
    
    module_ns['globals'] = module_ns
    module_ns.buildmode(False)
    
    await build_code_async(raw_code, module_ns, None, file=file)
    return module_ns

async def eval_file(fp, defaults=None, namespace=None):
    """

    :param fp: :class:`str` the file path to read and parse
    :param defaults: Optional[:class`dict`] defaults to be statically injected into the namespace before parsing the file
    :param namespace: Optional[:class:`PYKNamespace`] a pre-built namespace, useful to keep variables alive between evals
    :return: :class:`PYKNamespace`
    """
    with open(fp) as f:
        data = f.read()
    
    return await eval(data, defaults, namespace, file=fp)

