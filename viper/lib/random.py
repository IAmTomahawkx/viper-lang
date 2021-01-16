import random

from viper.objects import wraps_as_native, String, Integer

@wraps_as_native("Gets a random number between the two given numbers")
def _randint(lineno: int, runner, low: Integer, high: Integer):
    return Integer(random.randint(low._value, high._value), lineno, runner)

EXPORTS = {
    "randnum": _randint
}

MODULE_HELP = "A module to gets random numbers, choices, and the like"