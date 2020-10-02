from typing import *
from .ast import *
from .options import *
from .errors import *

__all__ = (
    "compile_ast",
    "split_lines"
)

def compile_ast(src: str, filename: str, configuration: Configuration = Configuration()) -> Tree:
    """
    compiles a source string into viper AST.
    :param src: the source string
    :type src: str
    :param filename: the name of the source
    :type filename: str
    :param configuration: the :class:`Configuration` to be used in parsing
    :type configuration: Configuration
    :return: :class:`Tree`
    """
    tree: Tree = Tree(configuration, filename, src)

    lines = split_lines(src, tree)
    # TODO: parse each block.
    # if its a lineholder -> parse it into ast
    # if its a blockholder -> parse the definer into ast and recursivly split lines

    return tree

def _compile(tree: Tree) -> None:
    pass

def split_lines(src: str, tree: Tree) -> List[Union[LineHolder, BlockHolder]]:
    _src: List[str] = src.splitlines()
    __src: List[str] = []
    for line in _src:
        __src.append(line.strip()) # remove indents and extra whitespace

    src = "\n".join(__src)
    del _src, __src

    resp: List[Union[LineHolder, BlockHolder]] = []

    block = ""
    blocked: Optional[Union[LineHolder, BlockHolder]] = None
    line_no = 1
    in_count = 0

    for index, char in enumerate(src):
        if char == "\n":
            if src[index+1] == tree.configuration.bracket_code_in:
                if not in_count:
                    # the next line is a code_in block, this will need to be a blockHolder
                    blocked = BlockHolder(line_no, block, "")
                    resp.append(blocked)
                    block = ""
                else:
                    # were already in a block
                    blocked.block += char

            elif src[index-1] == tree.configuration.bracket_code_in:
                if in_count < 2:
                    blocked = BlockHolder(line_no, block[0:len(block)-1].strip(), tree.configuration.bracket_code_in)
                    resp.append(blocked)
                    block = ""
                else:
                    blocked.block += char


            else:
                if block and not blocked:
                    blocked = LineHolder(line_no, block)
                    resp.append(blocked)
                    blocked = None
                    block = ""

                elif blocked:
                    blocked.block += char

            line_no += 1
            continue

        if not blocked:
            block += char

        elif isinstance(blocked, LineHolder):
            blocked.line += char

        else:
            blocked.block += char

        if char == tree.configuration.bracket_code_in:
            if not blocked:
                blocked = BlockHolder(line_no, block, char)

            in_count += 1

        elif char == tree.configuration.bracket_code_out:
            in_count -= 1
            if not in_count:
                blocked = None

    return resp

