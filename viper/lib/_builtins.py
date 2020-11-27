import inspect

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


EXPORTS = {
    "string": objects.String,
    "integer": objects.Integer,
    "bool": objects.Boolean,
    "say": say,
    "help": help
}