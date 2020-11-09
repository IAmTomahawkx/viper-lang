from viper import objects

@objects.wraps_as_native
def say(lineno, *args):
    rgs = []
    for arg in args:
        if not isinstance(arg, objects.String):
            try:
                arg = arg.__getattribute__("_cast")(objects.String)
            except:
                pass

        rgs.append(str(arg))

    print(*rgs)


EXPORTS = {
    "string": objects.String,
    "integer": objects.Integer,
    "bool": objects.Boolean,
    "say": say
}