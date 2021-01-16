from typing import Any
from viper import objects, errors
# try to import the faster json lib, if its been installed
try:
    import orjson as json
except ModuleNotFoundError:
    try:
        import ujson as json
    except ModuleNotFoundError:
        import json

def _recursively_wrap_objects(runner, lineno: int, obj: dict) -> dict:
    resp = {}
    for a, b in obj.items():
        if isinstance(b, objects.VPObject):
            resp[a] = b
        elif isinstance(b, dict):
            resp[a] = _recursively_wrap_objects(runner, lineno, b)
        elif isinstance(b, bool):
            resp[a] = objects.Boolean(b, lineno, runner)
        elif isinstance(b, (int, float)):
            resp[a] = objects.Integer(b, lineno, runner)
        elif isinstance(b, str):
            resp[a] = objects.String(b, lineno, runner)
        else:
            resp[a] = objects.PyObjectWrapper(runner, b)

    return resp

@objects.wraps_as_native("Loads a json string into a PyObjectWrapper. use .get to get values")
def load(lineno: int, runner, data: objects.String):
    resp = json.loads(data._value)
    return _recursively_wrap_objects(runner, lineno, resp)

@objects.wraps_as_native("Dumps a wrapped dictionary into a string. If the object is native has a _dumps method, the return value from that will be dumped")
def dump(lineno: int, runner, obj: Any) -> objects.String:
    if isinstance(obj, objects.PyNativeObjectWrapper):
        if isinstance(obj._obj, dict):
            obj = obj._obj
    elif isinstance(obj, objects.VPObject):
        if hasattr(obj, "_dump"):
            _obj = obj._dump()
            if not isinstance(_obj, dict):
                raise errors.ViperExecutionError(runner, lineno, f"<{obj._cast(objects.String, lineno)}> did not cast to a PyDict")

            obj = _obj
        else:
            raise errors.ViperExecutionError(runner, lineno,
                                             f"<{obj._cast(objects.String, lineno)}> cannot be casted to a PyDict")
    else:
        # huh?
        raise errors.ViperArgumentError(runner, lineno, f"Expected a wrapped PyDict, or a castable object, got {obj}")

    assert isinstance(obj, dict), errors.ViperArgumentError(runner, lineno, f"Expected a wrapped PyDict, or a castable object, got {obj}")
    stringed = json.dumps(obj)
    if isinstance(stringed, bytes):
        stringed = stringed.decode()

    return objects.String(stringed, lineno, runner)

EXPORTS = {
    "load": load,
    "dump": dump
}
MODULE_HELP = "Easily dump PyDicts using json.dump, and load json strings with json.load"