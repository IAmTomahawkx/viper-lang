import inspect
from typing import Union

from . import errors

def wraps_as_native(help: str = None):
    def wraps(func):
        if isinstance(func, type):
            def _wraps(*args, **kwargs):
                return PyNativeObjectWrapper(None, func(*args, **kwargs), help)
            return _wraps

        return PyNativeObjectWrapper(None, func, help)

    return wraps

class VPObject:
    __slots__ = "_runner", "_help"

    def __init__(self, runtime):
        self._runner = runtime
        self._help = None


    def __getattr__(self, item, from_execution=True):
        if item == "_cast":
            return self._cast

        elif item == "_help":
            return self._help

        if from_execution and item.startswith("_"):
            raise ValueError("Cannot access private values")

        return self.__getattribute__(item)

    def _cast(self, typ, lineno):
        if typ is String:
            return String(str(self), lineno, self._runner)

        raise errors.ViperCastError(self._runner, lineno, f"Cannot cast {self} to {typ}")


class NULL(VPObject):
    _help = "This is a constant object. null will be the same object everywhere."
    def __str__(self):
        return "null"
    
    __repr__ = __str__

class PyNativeObjectWrapper(VPObject):
    """
    a class to wrap objects that are designed to deal with viper objects.
    """
    def __init__(self, runtime, obj: object, help: str = None):
        super().__init__(runtime)
        self._obj = obj
        self._help = help
        if isinstance(obj, type(runtime)):
            raise ValueError

    def __str__(self):
        return f"<PyNativeWrappedObject_{self._obj}>"

    __repr__ = __str__

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
            return String(str(self._obj), lineno, self._runner)
        elif typ is Integer:
            return Integer(int(self._obj), lineno, self._runner)
        elif typ is Boolean:
            return Boolean(bool(self._obj), lineno, self._runner)
        else:
            raise ValueError(f"Cannot cast {self!r} to {typ.__name__}")

    async def _call(self, runner, line, *args):
        item = self._obj
        if not callable(item):
            raise errors.ViperExecutionError(runner, line, f"<PyObject_{item}> is not callable")

        if inspect.iscoroutine(item) or inspect.iscoroutinefunction(item):
            resp = await item(line, runner, *args)
        else:
            resp = item(line, runner, *args)

        if not isinstance(resp, VPObject):
            resp = PyObjectWrapper(runner, resp)

        return resp

class PyObjectWrapper(PyNativeObjectWrapper):
    """
    a wrapper that attempts to maintain some sort of consistency between python objects and viper objects
    """
    def __init__(self, *args):
        super(PyObjectWrapper, self).__init__(*args)
        import viper.runner as runner
        if isinstance(self._obj, runner.Runtime):
            raise ValueError
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
                resp = String(resp, line, runner)
            elif isinstance(resp, bool):
                resp = Boolean(str(resp), line, runner)
            elif isinstance(resp, (int, float)):
                resp = Integer(resp, line, runner)
            else:
                resp = PyObjectWrapper(runner, resp)

        return resp

    def __getattr__(self, item):
        obj = super().__getattr__(item)
        if not isinstance(obj, VPObject):
            return PyObjectWrapper(self._runner, obj)

        return obj

    def _cast(self, typ, lineno):
        if typ is String:
            if isinstance(self._obj, (dict, list)):
                return String(str(self._obj), lineno, self._runner)
        else:
            return String(f"<PyWrappedObject_{self._obj}>", lineno, self._runner)

    def __str__(self):
        # sometimes this gets called by wrapped objects while printing, such as when in a dict.
        # It can return an actual string, cause its not being accessed by the viper code
        return f"<PyWrappedObject_{self._obj}>"

    __repr__ = __str__

class Module(VPObject):
    __slots__ = "_mod", "_name", "_dir"
    def __init__(self, name: str, py_mod, runtime):
        self._mod = py_mod
        self._dir = py_mod.EXPORTS
        self._name = name
        super().__init__(runtime)
        self._help = getattr(py_mod, "MODULE_HELP", "This module has no help").strip()

    def __getattr__(self, item):
        if item == "_cast":
            return self._cast

        if item in self._dir:
            return self._dir[item]

        super().__getattr__(item)

    def _cast(self, typ, lineno):
        if typ is String:
            return String(str(self), lineno, self._runner)
        raise errors.ViperCastError(self._runner, lineno, f"Cannot cast modules to {typ.__name__}")

    def __repr__(self):
        return f"<Module '{self._name}'>"

    __str__ = __repr__

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

    def _copy(self):
        return self.__class__(self._value, self.lineno, self._runner)

class String(Primary):
    _help = "strings are used to represent text"
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

    def __eq__(self, other):
        if not isinstance(other, String):
            return False

        return self._value == other._value

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

    def __eq__(self, other):
        if not isinstance(other, Integer):
            return False

        return self._value == other._value

class Boolean(Primary):
    def __init__(self, value, lineno: int, runner):
        self.lineno = lineno
        self._runner = runner
        if isinstance(value, str):
            self._value = value.lower() == "true"
        else:
            self._value = value

    def _cast(self, typ, lineno):
        if typ is Boolean:
            return self

        return super()._cast(typ, lineno)

    def __eq__(self, other):
        if not isinstance(other, Boolean):
            return False

        return self._value == other._value


class Function(VPObject):
    def __init__(self, ast, runner):
        self._ast = ast
        self._ast.matches.append(self)
        self._runner = runner

    def __getattr__(self, item):
        return self.__getattribute__(item)

    def __repr__(self):
        return self._ast.__repr__()

    def _cast(self, typ, lineno):
        raise errors.ViperCastError(self._runner, lineno, "Cannot cast Functions")

    async def _call(self, runner, args):
        return await self._ast.execute(runner, args)

class VPList(VPObject):
    __slots__ = "_lineno", "_list", "_max_length"
    def __init__(self, lineno: int, runner, default: list = None):
        super(VPList, self).__init__(runner)
        self._lineno = lineno
        self._list = default or list()
        self._max_length = None

    def append(self, _, lineno: int, item: VPObject):
        """
        adds the given item to the list.
        Raises ExecutionError if the list has a size limit and is full
        """
        if self._max_length is not None and self._length == self._max_length:
            raise errors.ViperExecutionError(self._runner, lineno, "List is full")

        self._list.append(item)
        self._length += 1

    def appendMany(self, _, lineno: int, *items: list):
        """
        adds the given items to the list.
        Raises ExecutionError if the list has a size limit and adding the items would cause it to go over this limit.
        """
        if not items:
            raise errors.ViperArgumentError(self._runner, lineno, "Expected at least 1 argument")

        if self._max_length and len(items) + self.length(None, None) > self._max_length:
            raise errors.ViperExecutionError(self._runner, lineno, "List is full")


        for item in items:
            self._list.append(item)


    def get(self, _, lineno: int, index: Integer):
        """
        returns the item at the index.
        Raises ExecutionError if the index is invalid.
        Raises ArgumentError if the argument is not an integer
        """
        if not isinstance(index, Integer):
            raise errors.ViperArgumentError(self._runner, lineno, f"Expected an integer, got {index}")
        try:
            return self._list[int(index._value)]
        except IndexError:
            if self._list:
                error = f"The given index was out of range (valid index: 0-{len(self._list)}, got {index._value})"
            else:
                error = f"The given index was out of range (valid index: <List is empty>)"
            raise errors.ViperExecutionError(self._runner, lineno, error)

    def remove(self, _, lineno: int, index: Integer):
        """
        removes and returns the item at the given index
        Raises ExecutionError if the index is invalid.
        Raises ArgumentError if the argument is not an integer
        """
        if not isinstance(index, Integer):
            raise errors.ViperArgumentError(self._runner, lineno, f"Expected an integer, got {index}")

        try:
            value = self._list.pop(int(index._value))
        except IndexError:
            if self._list:
                error = f"The given index was out of range (valid index: 0-{len(self._list)}, got {index._value})"
            else:
                error = f"The given index was out of range (valid index: <List is empty>)"
            raise errors.ViperExecutionError(self._runner, lineno, error)

        else:
            return value

    def length(self, _, __):
        return len(self._list)

    def copy(self, _, __):
        new = VPList.__new__(VPList)
        new._runner = self._runner
        new._list = self._list.copy()
        new._max_length = self._max_length
        return new

    def clear(self, _, __):
        self._list.clear()

class VPDictionary(VPObject):
    __slots__ = "_dict", "_lineno"
    def __init__(self, lineno: int, runner, default: dict = None):
        self._lineno = lineno
        super(VPDictionary, self).__init__(runner)
        self._dict = default or dict()

    def _cast(self, typ, lineno):
        if typ is String:
            return str(self._dict)

        raise errors.ViperCastError(self._runner, lineno, f"Cannot cast {self} to {typ}")

    def clear(self, runner, lineno: int):
        """
        Clears the dictionary, removing every key
        """
        self._dict.clear()
        return runner.null

    def set(self, runner, lineno: int, key: Union[String, Integer], value: VPObject):
        """
        Sets a value to a key, allowing you to pass the same key to .get to access the value
        """
        if not isinstance(key, (String, Integer)):
            raise errors.ViperExecutionError(runner, lineno,
                                             f"Expected a String or an Integer as a key, got {key._cast(String, lineno)}")

        self._dict[key] = value
        return runner.null

    def contains(self, runner, lineno: int, key: Union[String, Integer]):
        """
        Returns a bool indicating if a certain key exists in the dictionary
        """
        if not isinstance(key, (String, Integer)):
            raise errors.ViperExecutionError(runner, lineno,
                                             f"Expected a String or an Integer as a key, got {key._cast(String, lineno)}")

        return Boolean(key in self._dict, lineno, runner)

    def get(self, runner, lineno: int, key: Union[String, Integer], fallback: VPObject = None):
        """
        Gets the value of a key.
        """
        if not isinstance(key, (String, Integer)):
            raise errors.ViperExecutionError(runner, lineno,
                                             f"Expected a String or an Integer as a key, got {key._cast(String, lineno)}")

        return self._dict.get(key, default=fallback) or runner.null

    def length(self, runner, lineno: int):
        return Integer(len(self._dict), lineno, runner)

    def update(self, runner, lineno, other):
        pass