import sly

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

        IMPORT
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

    ignore = ' \t'

    @_(r"\n+")
    def EOL(self, t):
        self.lineno += t.value.count('\n')
        return t

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1
