import inspect

from . import errors

def wraps_as_native(func):
    return PyNativeObjectWrapper(None, func)

class VPObject:
    __static = False
    def __init__(self, runtime):
        self._runner = runtime


    def __getattr__(self, item):
        if item == "_cast":
            return self._cast

        if item.startswith("_"):
            raise ValueError("Cannot access private values")

        return self.__getattribute__(item)

    def _cast(self, typ, lineno):
        if typ is String:
            return String(str(self), lineno, self._runner)

        raise errors.ViperCastError(self._runner, lineno, f"Cannot cast {self} to {typ}")


class NULL(VPObject):
    def __str__(self):
        return "null"
    
    __repr__ = __str__

class PyNativeObjectWrapper(VPObject):
    """
    a class to wrap objects that are designed to deal with viper objects.
    """
    def __init__(self, runtime, obj: object):
        super().__init__(runtime)
        self._obj = obj

    def __getattr__(self, item: str):
        if item.startswith("_"):
            raise ValueError("Cannot access private values")

        return getattr(self._obj, item)

    def __dir__(self):
        dirs = super().__dir__()
        dirs = [d for d in dirs if not d.startswith("_")]  # hide attributes that cant be accessed
        return dirs

    def _cast(self, typ, lineno):
        if typ is String:
            return String(str(self._obj))
        elif typ is Integer:
            return Integer(int(self._obj))
        elif typ is Boolean:
            return Boolean(bool(self._obj))
        else:
            raise ValueError(f"Cannot cast {self!r} to {typ.__name__}")

    async def _call(self, runner, line, *args):
        item = self._obj
        if not callable(item):
            raise errors.ViperExecutionError(runner, line, f"<PyObject_{item}> is not callable")

        if inspect.iscoroutine(item) or inspect.iscoroutinefunction(item):
            resp = await item(line, *args)
        else:
            resp = item(line, *args)

        if not isinstance(resp, VPObject):
            resp = PyObjectWrapper(runner, resp)

        return resp

class PyObjectWrapper(PyNativeObjectWrapper):
    """
    a wrapper that attempts to maintain some sort of consistency between python objects and viper objects
    """
    async def _call(self, runner, line, *args):
        item = self._obj
        if not callable(item):
            raise errors.ViperExecutionError(runner, line, f"<PyWrappedObject_{item}> is not callable")

        _args = []
        for arg in args:
            if isinstance(arg, Primary):
                _args.append(arg._value)
            else:
                _args.append(arg)

        if inspect.iscoroutine(item) or inspect.iscoroutinefunction(item):
            resp = await item(*_args)
        else:
            resp = item(*_args)

        if not isinstance(resp, VPObject):
            if isinstance(resp, str):
                resp = String(resp)
            elif isinstance(resp, bool):
                resp = Boolean(str(resp))
            elif isinstance(resp, (int, float)):
                resp = Integer(resp)
            else:
                resp = PyObjectWrapper(runner, resp)

        return resp

class Primary(VPObject):
    __slots__ = "_value", "lineno", "_runner"
    def __init__(self, value, lineno: int, runner):
        self._value = value
        self.lineno = lineno
        self._runner = runner

    def __repr__(self):
        return f"<{self.__class__.__name__} {self._value}>"

    def __str__(self):
        return str(self._value)

class String(Primary):
    def __init__(self, val, lineno: int, runner):
        self._value = val.strip('"')
        self.lineno = lineno
        self._runner = runner

    def _cast(self, typ, lineno):
        if typ is String:
            return self

        return super()._cast(typ, lineno)

    def __add__(self, other):
        assert isinstance(other, String), errors.ViperTypeError(self._runner, self.lineno, f"Cannot combine string and {other}")
        return String(self._value + other.__getattribute__("_value"), self.lineno, self._runner)

class Integer(Primary):
    def __init__(self, value, lineno: int, runner):
        self.lineno = lineno
        self._runner = runner
        try:
            self._value = int(value)
        except:
            self._value = float(value)

    def _cast(self, typ, lineno):
        if typ is Integer:
            return self

        return super()._cast(typ, lineno)

class Boolean(Primary):
    def __init__(self, value, lineno: int, runner):
        self.lineno = lineno
        self._runner = runner
        self._value = value.lower() == "true"

    def _cast(self, typ, lineno):
        if typ is Boolean:
            return self

        return super()._cast(typ, lineno)


class Function(VPObject):
    def __init__(self, ast, runner):
        self._ast = ast
        self._runner = runner

    def _cast(self, typ, lineno):
        raise errors.ViperCastError(self._runner, lineno, "Cannot cast Functions")

    async def _call(self, runner, args):
        return await self._ast.execute(runner, args)