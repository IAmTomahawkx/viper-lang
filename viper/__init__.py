from .runner import Runtime
from .scope import Scope, InitialScope
from . import objects
from .objects import String, Integer, Boolean
from .errors import *

from typing import Union
from os import PathLike as _PathLike
from io import FileIO as _FileIO

__version__ = "1.0.0"

async def eval(code: str, filename="<string>", injected: dict=None, runtime: Runtime=None) -> Runtime:
    """
    Evaluates the passed code in the viper runtime. This is a basic entrypoint into running viper code.

    Parameters
    -----------
    code: :class:`str`
        the code to evaluate
    filename: Optional[:class:`str`]
        the filename of the code you are running from. Useful in tracebacks. Defaults to "<string>"
    injected: Optional[:class:`dict`]
        a dictionary of variables to inject into the namespace before evaluating the code.
    runtime: Optional[:class:`Runtime`]
        a pre-existing runtime to use instead of creating one

    Returns
    --------
    :class:`Runtime` the :class:`Runtime` that the code was evaluated with
    """
    if runtime and injected:
        runtime._injected.update(injected)

    runtime = runtime or Runtime(filename, injected)
    await runtime.run(code)
    return runtime

async def eval_file(fp: Union[_PathLike, str, _FileIO], filename: str=None, injected: dict=None, runtime: Runtime=None) -> Runtime:
    """
    A quicker way to evaluate files. Reads the given file and evaluates the contents.

    Parameters
    -----------
    fp: Union[:class:`os.PathLike`, :class:`str`, :class:`io.FileIO`]
        the file path or object to read from
    filename: Optional[:class:`str`]
        the name of the file. Defaults to the name of the file.
    injected: Optional[:class:`dict`]
        a dictionary of variables to inject into the namespace before evaluating the code.

    Returns
    --------
    :class:`Runtime` the :class:`Runtime` that the code was evaluated with

    """
    if isinstance(fp, (_PathLike, str)):
        with open(fp, mode="r", encoding="utf8") as file:
            code = file.read()
            filename = filename or str(fp)
    else:
        code = fp.read()
        filename = filename or fp.name

    return await eval(code, filename, injected=injected, runtime=runtime)
