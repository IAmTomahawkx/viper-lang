VP_NONE = None

class VPObject:
    __static = False
    def __init__(self, runtime):
        self._runtime = runtime


    def __getattr__(self, item):
        if item == "_cast":
            return self._cast

        if item.startswith("_"):
            raise ValueError("Cannot access private values")

        return self.__getattribute__(item)

    def _cast(self, typ):
        if typ is String:
            return str(self)


class NULL(VPObject):
    def __str__(self):
        return "null"
    
    __repr__ = __str__


class PyObjectWrapper(VPObject):
    def __init__(self, runtime, obj: object):
        super().__init__(runtime)
        self._obj = obj

    def __getattr__(self, item: str):
        if item.startswith("_"):
            raise ValueError("Cannot access private values")

        return getattr(self._obj, item)

    def __dir__(self):
        dirs = super().__dir__()
        dirs = [d for d in dirs if not d.startswith("_")] # hide attributes that cant be accessed
        return dirs

    def _cast(self, typ):
        if typ is String:
            return String(str(self._obj))
        elif typ is Integer:
            return Integer(int(self._obj))
        elif typ is Boolean:
            return Boolean(bool(self._obj))
        else:
            raise ValueError(f"Cannot cast {self!r} to {typ.__name__}")

class Primary(VPObject):
    def __init__(self, value):
        self._value = value

    def __repr__(self):
        return f"{self.__class__.__name__!r} {self._value}"

    def __str__(self):
        return str(self._value)

class String(Primary):
    def _cast(self, typ):
        if typ is String:
            return self

        super()._cast(typ)

class Integer(Primary):
    def _cast(self, typ):
        if typ is Integer:
            return self

        super()._cast(typ)

class Boolean(Primary):
    def _cast(self, typ):
        if typ is Boolean:
            return self

        super()._cast(typ)
