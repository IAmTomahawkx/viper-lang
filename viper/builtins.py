import random
import os
from typing import Union, Any

from .objects import VP_NONE, VP_Error
from .errors import VP_ArgumentError


def read(filepath: str) -> Union[str, type(VP_NONE)]:
    """
    reads a file and returns the contents (not a byte file)
    :param filepath: :class:`str` the filepath to read
    :return: :class:`str` the file contents
    """
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return f.read()

    else:
        return VP_NONE


def randline(filepath: str) -> Union[str, type(VP_NONE)]:
    """
    Reads a file and returns a random line
    :param filepath: :class:`str` the filepath to read
    :return: :class:`str` or :class:`VP_NONE` if the file is empty
    """
    if os.path.exists(filepath):
        with open(filepath) as f:
            lines = f.readlines()
            if not lines:
                return VP_NONE

            return random.choice(lines)

    else:
        return VP_NONE


def write(filepath: str, content: str) -> type(VP_NONE):
    """
    writes the content to the given filepath
    :param filepath: the file to write to
    :param content:
    :return: :class:`VP_NONE`
    """
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    with open(filepath, "w") as f:
        f.write(content)

    return VP_NONE

def add_line(filepath: str, content: str) -> type(VP_NONE):
    """
    adds a line to a pre-existing file
    :param filepath: :class:`str` the file path to write to
    :param content: :class:`str` the content to write
    :return: :class:`VP_NONE`
    """
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    with open(filepath, "a") as f:
        f.write(content)

    return VP_NONE

def randnum(min: int, max: int) -> int:
    """
    returns a random number between the min and max
    :param min: :class:`int` the minimum number to return
    :param max: :class:`int` the maximum number to return
    :return: :class:`int` the chosen number
    """
    return random.randint(min, max)

def choice(*choices: Any) -> Any:
    """
    returns a random choice from the given input. takes any number of arguments.
    :param choices: the choices to pick from
    :return: Any. the chosen item from the input arguments. returns :class:`VP_NONE` if no arguments given
    """
    if not choices:
        return VP_NONE
    
    return random.choice(choices)

def say(*args):
    """
    prints the given text to the console.
    :param args:
    :return:
    """
    print(*args)
    return VP_NONE

def to_num(s):
    try:
        return int(s)
    except:
        return float(s)

def stack(error: VP_Error):
    """
    utility for getting a traceback from an error
    :param error: the error
    :return: str
    """
    if not isinstance(error, VP_Error):
        raise VP_ArgumentError("expected an error, got {0!r}".format(error))

    return error.format_stack()

def fmt(string: str, *args, **kwargs):
    return string.format(*args, **kwargs)


safe_builtins = {
    "say": say,
    "string": str,
    "boolean": bool,
    "number": to_num,
    "choice": choice,
    "randnum": randnum,
    "stack": stack,
    "format": fmt
}

unsafe_builtins = {
    "read": read,
    "write": write,
    "writeline": add_line,
    "readrandline": randline,
    **safe_builtins
}

def get_builtins(safety=False):
    if safety:
        return {a: (b, False) for a, b in safe_builtins.items()}

    return {a: (b, False) for a, b in unsafe_builtins.items()}

