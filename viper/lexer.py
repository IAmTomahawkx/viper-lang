import sly
from . import errors

class ViperLexer(sly.Lexer):
    tokens = (
        STATIC,
        FUNC,

        IF,
        ELIF,
        ELSE,

        EOL,

        PLUS,
        MINUS,
        MULTIPLY,
        DIVIDE,
        MODULUS,

        IS,
        NOT,

        EQ,
        NE,
        GE,
        GT,
        LE,
        LT,

        EQUALS,
        COMMA,

        CAST,

        BLOCK_OPEN,
        BLOCK_CLOSE,
        PAREN_OPEN,
        PAREN_CLOSE,

        QMARK,
        DECIMAL,
        STRING,

        ATTR,

        TRUE,
        FALSE,
        NONE,
        RETURN,
        NULL,

        IDENTIFIER,

        IMPORT,
        CATCH,
        THROW,
        TRY
    )
    ignore_comment = r'\/\/.*'

    PLUS = r'\+'
    MINUS = r'-'
    MULTIPLY = r'\*'
    DIVIDE = r'/'
    MODULUS = '%'

    EQ = '=='
    NE = '!='
    GE = '>='
    GT = '>'
    LE = '<='
    LT = '<'

    NOT = "isnot"

    ELIF = "else if"

    CAST = "as"
    ATTR = r'\.'
    QMARK = r'\?'
    EQUALS = r"\="
    COMMA = r"\,"


    BLOCK_OPEN = r"\{"
    BLOCK_CLOSE = r"\}"
    PAREN_OPEN = r"\("
    PAREN_CLOSE = r"\)"

    DECIMAL = r'[0-9]+'
    STRING = r'".*?(?<!\\)(?:\\\\)*?"'

    IDENTIFIER = r'[a-zA-Z_0-9]+'

    IDENTIFIER['static'] = STATIC
    IDENTIFIER['return'] = RETURN
    IDENTIFIER['true'] = TRUE
    IDENTIFIER['false'] = FALSE
    IDENTIFIER['none'] = NONE
    IDENTIFIER['true'] = TRUE
    IDENTIFIER['false'] = FALSE
    IDENTIFIER['func'] = FUNC
    IDENTIFIER['equals'] = "EQUALS"
    IDENTIFIER['if'] = IF
    IDENTIFIER['elif'] = "ELIF"
    IDENTIFIER['else'] = ELSE
    IDENTIFIER['import'] = IMPORT
    IDENTIFIER['is'] = IS
    IDENTIFIER['isnot'] = "NOT"
    IDENTIFIER['catch'] = CATCH
    IDENTIFIER['throw'] = THROW
    IDENTIFIER['try'] = TRY

    ignore = ' \t'

    @_(r"\n+")
    def EOL(self, t):
        self.lineno += t.value.count('\n')
        return t

    def error(self, t):
        raise errors.ViperSyntaxError(t, 0, "Illegal character '%s'" % t.value[0])
