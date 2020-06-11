from .__init__ import build_code as pykeval, PYKNamespace
from .builtins import builtins

def pyk_repl():
    ns = PYKNamespace()
    ns.buildmode(True)
    ns.update(builtins)
    ns['namespace'] = ns
    ns.buildmode(False)
    
    while True:
        line = input(">> ")
        if "{" in line:
            count = 1
            while count > 0:
                newline = input(".. ")
                if "{" in line:
                    count += 1
                if "}" in line:
                    count -= 1
                line += "\n" + newline
        try:
            ret = pykeval(line, ns, None)
        print(ret)

pyk_repl()
