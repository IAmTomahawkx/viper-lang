# PYK
pyk is a simple, easy to understand language with easy integration capabilities.

## Install
pyk is not available through pypi, install can be done through the following:
```
pip install -U git+https://github.com/IAmTomahawkx/pyk
```
and can be imported into your project
```python
import pyk
```

## Python Usage
To use pyk in your application, make use of the two eval methods, pyk.eval and pyk.eval_file functions
```python
import pyk
code = '$myvar = "hi"'
pyk.eval(code)
```
or
```python
import pyk
pyk.eval_file("myfile.pyk")
```

you can also pass defaults to be injected into the namespace, as such
```python
import pyk
pyk.eval("say($myvar)", {"myvar": "blue"})
```
another way to pass defaults is to pass a pyk namespace to the eval
```python
import pyk
namespace = pyk.PYKNamespace()
namespace['myvar'] = "blue"

# creating a static variable
namespace['mystaticvar'] = "red", True

pyk.eval("say($myvar)", namespace=namespace)
```

# Syntax
## variables
variables are set like in python, but with a dollar sign ($) in front of the name. variables are retrieved in the same way,
the name with a dollar sign ($) in front. variables can be marked as `static` by putting `static ` in front of the variable
name. static variables cannot be changed by anything other than intervention in python code
```
$myvar = "red"

static $mystaticvar = "blue"

$mystaticvar = "hello"  <-- StaticError
```

## functions
functions are created either in python and passed to the namespace, or in pyk. functions created in pyk follow this syntax
```
func myfunc() {
    return
}
```
quite similar to python, with a few key differences. you may put `static ` in front of the `func` keyword to mark the function as static,
preventing it from being reassigned.
```
static func myfunc() {
    return
}
```
arguments look like the following
```
func myfunc(argument1, argument2) {
    return
}
```
an argument can be made optional by inserting a question mark (?) in front of the argument name, E.x.
```
func myfunc(argument1, ?optional_arg1) {
    return
}
```
optional arguments that are not given will be passed as a `none` object (note that this is not the same as a python `None`)

functions are called the same as in python:
```
func myfunc() {
    return
}
myfunc()
```

## builtins
there are several built in functions that will be available inside of pyk. They can be seen in the `pyk/builtins.py` file.
there are a couple builtin not defined in this file, the `namespace` variable, which points back to the global namespace.
there is also `true` / `false`, which are the pyk booleans (AKA python booleans).

## a full example
```
static $globalvar = "hi"

func name(arg, ?arg1) {
    $var = 1
    if ($var is 1) {
        $var += 1
    }
    else if ($var is not 1) {
        $var = "stuff"
    }
    default {
        $var = none
    }
}

func main() {
    say("hi")
    name("hello")
}
main()
```

# Customizing pyk
most of pyk can be edited by editing `pyk/keywords.py` file. Most of the options are pretty self explanatory.
