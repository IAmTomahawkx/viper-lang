.. image:: https://travis-ci.org/IAmTomahawkx/viper-lang.svg?branch=master
    :target: https://travis-ci.org/IAmTomahawkx/viper-lang
    :alt: Build Status
.. image:: https://discord.com/api/guilds/561043858402836482/embed.png
   :target: https://discord.gg/cEAxG8A
   :alt: Discord server invite
.. image:: https://img.shields.io/pypi/v/viper-lang.svg
   :target: https://pypi.python.org/pypi/viper-lang
   :alt: PyPI version info
.. image:: https://img.shields.io/pypi/pyversions/viper-lang.svg
   :target: https://pypi.python.org/pypi/viper-lang
   :alt: PyPI supported Python versions

Viper
=====
Viper is a simple, easy to understand language with easy integration capabilities.

Install
--------
| Viper is available for python 3.6+.
| Viper is now on pypi! It can be installed via

.. code:: sh

    python -m pip install viper-lang

The dev version can be installed via

.. code:: sh

    python -m pip install -U git+https://github.com/IAmTomahawkx/viper-lang

And can be imported into your project

.. code:: py

    import viper

Python Usage
-------------
To use Viper in your application, make use of the two eval methods, viper.eval and viper.eval_file functions. These functions
are asynchronous, and must be run using asyncio, whether that be through the `await` keyword, or something such as `asyncio.run`. \
The asyncio docs can be found `here <https://docs.python.org/3/library/asyncio.html#module-asyncio/>`_.

.. code-block:: python

    import viper
    import asyncio
    code = 'myvar = "hi"'
    asyncio.run(viper.eval(code))

or

.. code-block:: python

    import asyncio
    import viper
    asyncio.run(viper.eval_file("myfile.vp"))

you can pass defaults to be injected into the namespace, as such

.. code-block:: python

    import asyncio
    import viper
    asyncio.run(viper.eval("say(myvar)", injected={"myvar": "blue"}))

for more control over the creation, you can create your own `viper.Runtime` instance

.. code-block:: python

    import asyncio
    import viper

    runtime = viper.Runtime("<input>", injected={"myvar": "blue"}, allow_unsafe_imports=False)
    code = "say(myvar)"
    asyncio.run(runtime.run(code))

You can use this to disable features like unsafe modules, such as the `requests` module, or the `files` module.

.. code-block:: python

    import asyncio
    import viper

    runtime = viper.Runtime("<input>", allow_unsafe_imports=False)
    code = "import files"
    asyncio.run(runtime.run(code))

The above will raise a ViperModuleError.


Syntax
---------

Variables
~~~~~~~~~~
variables are set like in python, but with a dollar sign ($) in front of the name. variables are retrieved in the same way,
the name with a dollar sign ($) in front. variables can be marked as `static` by putting `static` in front of the variable
name. static variables cannot be changed by anything other than intervention in python code

.. code-block::

    myvar = "red"

    static mystaticvar = "blue"

    mystaticvar = "hello"  <-- StaticError

functions
~~~~~~~~~~

functions are created either in python and passed to the namespace, or in viper. functions created in viper follow this syntax

.. code-block::

    func myfunc() {
        return
    }

quite similar to python, with a few key differences. you may put `static ` in front of the `func` keyword to mark the function as static,
preventing it from being reassigned.

.. code-block::

    static func myfunc() {
        return
    }

arguments look like the following

.. code-block::

    func myfunc(argument1, argument2) {
        return
    }

an argument can be made optional by inserting a question mark (?) in front of the argument name, E.x.

.. code-block::

    func myfunc(argument1, ?optional_arg1) {
        return
    }

optional arguments that are not given will be passed as a `none` object (note that this is not the same as a python `None`)

functions are called the same as in python:

.. code-block::

    func myfunc() {
        return
    }
    myfunc()

builtins
~~~~~~~~~
the viper namespace is left quite empty by default. The following are included in the default namespace:
- say(\*args) - equivilant to `print` in python.
- help(obj) - prints an objects help.
- dir(obj) - lists all attributes an object has.

Types are included in the namespace:
- `string`
- `integer`
- `bool`
- `dictionary`
- `list`

there is also `true` / `false`, which are the booleans.

a full example
----------------

.. code-block::

    static globalvar = "hi"

    func name(arg, ?arg1) {
        var = 1
        if (var is 1) {
            var += 1
        }
        elif (var is not 1) {
            var = "stuff"
        }
        else {
            var = none
        }
    }

    func main() {
        say("hi")
        name("hello")
    }
    main()

Discord.py integration
-----------------------
to make things easier, the `viper.exts.discord` module makes it easy to pass safe objects, with limited accessibility, to viper,
making it easy to pass discord.py models (indirectly) to your users, without fear of leaking your token and/or other sensitive data. \
Simply pass a discord.py model to its respective `exts.discord` counterpart, and pass that to your viper namespace
