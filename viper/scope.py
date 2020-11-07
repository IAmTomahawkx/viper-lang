from .ast import Ide

class Scope:
    def __init__(self, runtime):
        self._vars = {}
        self._runtime = runtime

    def set_var(self, item, value):
        pass