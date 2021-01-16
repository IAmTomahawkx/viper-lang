import inspect
from typing import Union

from viper import objects

@objects.wraps_as_native("says a line in the terminal")
def say(lineno, runner, *args):
    rgs = []
    for arg in args:
        if not isinstance(arg, objects.String):
            try:
                arg = arg.__getattribute__("_cast")(objects.String, lineno)
            except:
                arg = "<Could not cast to string>"

        rgs.append(str(arg))

    print(*rgs)

@objects.wraps_as_native("shows help on an object")
def help(lineno, runner, obj=None):
    if obj is None:
        val = """
        Use `help(<some object>)` to get help on that object.
        
        """
        return objects.String(inspect.cleandoc(val), lineno, runner)

    if not isinstance(obj, objects.VPObject):
        return objects.String("This object has no help", lineno, runner)

    if not obj._help:
        return objects.String("This object has no help", lineno, runner)

    return objects.String(obj._help, lineno, runner)

@objects.wraps_as_native("Lists out the contents of a module or wrapped PyClass")
def dirobj(lineno, runner, obj: Union[objects.PyObjectWrapper, objects.Module]):
    if isinstance(obj, objects.Module):
        return objects.VPDictionary(lineno, runner, default=obj._dir)
    return runner.null

EXPORTS = {
    "string": objects.String,
    "integer": objects.Integer,
    "bool": objects.Boolean,
    "dictionary": objects.VPDictionary,
    "list": objects.VPList,
    "say": say,
    "help": help,
    "dir": dirobj
}