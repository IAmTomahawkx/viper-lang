import random

from .keywords import PYK_KEYWORDS
from .objects import PYK_NONE

def read(filepath):
    with open(filepath) as f:
        return f.read()

def randline(filepath):
    with open(filepath) as f:
        lines = f.readlines()
        if not lines:
            return PYK_NONE
        
        return random.choice(lines)

def write(filepath, content):
    with open(filepath, "w") as f:
        f.write(content)
    return PYK_NONE

def add_line(filepath, content):
    with open(filepath, "a") as f:
        f.write(content)
    return PYK_NONE

def randnum(min, max):
    return random.randint(min, max)

def choice(*choices):
    if not choices:
        return PYK_NONE
    
    return random.choice(choices)

def say(*args):
    print(*args)
    return PYK_NONE

def to_num(s):
    try:
        return int(s)
    except:
        return float(s)

builtins = {
    "read": read,
    "write": write,
    "say": say,
    "string": str,
    "boolean": bool,
    "number": to_num,
    "choice": choice,
    "randnum": randnum,
    "writeline": add_line,
    "readrandline": randline
}

