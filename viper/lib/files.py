import os
from viper import objects, errors

@objects.wraps_as_native("Reads content from a file. Takes only a file path")
def open_file(lineno, runner, fp: objects.String):
    fp = fp._value
    if not os.path.exists(fp):
        raise errors.ViperExecutionError(runner, lineno, f"File {fp} does not exist")

    with open(fp) as f:
        return objects.String(f.read(), lineno, runner)

@objects.wraps_as_native("Writes content to a file. Takes a file path and a string ")
def write_file(lineno, runner, fp: objects.String, content: objects.String):
    fp = fp._value
    content = content._value
    try:
        with open(fp, mode="w") as f:
            f.write(content)
    except Exception as e:
        raise errors.ViperExecutionError(runner, lineno, *e.args)

    return runner.null

@objects.wraps_as_native("Tells you wether or not a file exists")
def exists_file(lineno, runner, fp: objects.String):
    fp = fp._value
    return objects.Boolean(os.path.exists(fp), lineno, runner)

@objects.wraps_as_native("Wether the given path is a directory or not")
def is_dir(lineno, runner, fp: objects.String):
    fp = fp._value
    return objects.Boolean(os.path.isdir(fp), lineno, runner)


EXPORTS = {
    "read": open_file,
    "write": write_file,
    "exists": exists_file,
    "isdir": is_dir
}
MODULE_HELP = """
A module to enable basic file-related activities such as reading and writing
"""