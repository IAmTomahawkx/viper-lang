.. image:: https://img.shields.io/pypi/v/viper-lang.svg
   :target: https://pypi.python.org/pypi/viper-lang
   :alt: PyPI version info

Viper Changelog
================

V0.0.2
--------
- Fixed a parsing bug where ``if`` statements would skip parsing of the line below the code block, IE

.. code::

    if (1 is 1) {
        say("obviously this is true")
    } else {
        say("this isn't possible!")
    }
    $var = "hi" //this line would get skipped

- fixed the readme stating that ``else`` was ``default``
- fixed the ``return`` statement raising StopIteration instead of StopAsyncIteration in python, causing a RuntimeError because it's in an async function
- changed the "something isn't right" text when the line can't be parsed to the more appropriate "SyntaxError: line"

V0.0.1
----------
Initial release