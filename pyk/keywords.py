PYK_KEYWORDS = {
    "PYK_STATIC": "static",
    "PYK_FUNC": "func",
    "PYK_NULL": "None",
    
    "PYK_IF": "if",
    "PYK_ELIF": "else if",
    "PYK_ELSE": "else",
    
    "PYK_FALSE": "false",
    "PYK_TRUE": "true",
    
    "PYK_NAMESPACE": "$namespace",
    "PYK_RETURN": "return",
    
    "PYK_EQUALS": ["is", "=="],
    "PYK_NOT_EQUALS": ["is not", "!="],
    "PYK_GREATER": ">",
    "PYK_SMALLER": "<",
    "PYK_CONTAINS": "in",
    "PYK_NOTCONTAINS": "!in",
    
    "PYK_VARMARKER": "$",
    
    "PYK_COMMENT": "//",

    "PYK_TRY": "try",
    "PYK_CATCH": "error",
    "PYK_THROW": "raise"
}

# don't touch this one
PYK_STRICT_PARSING_KEYWORDS = [
    PYK_KEYWORDS['PYK_FUNC'],
    PYK_KEYWORDS['PYK_STATIC'],
    PYK_KEYWORDS['PYK_RETURN']
]

PYK_BRACKETS = {
    "PYK_CODE_IN": "{",
    "PYK_CODE_OUT": "}",
    "PYK_FUNCTIONARGS_IN": "(",
    "PYK_FUNCTIONARGS_OUT": ")",
    "PYK_FUNCTIONCALL_IN": "(",
    "PYK_FUNCTIONCALL_OUT": ")",
    "PYK_CONDITIONAL_IN": "(",
    "PYK_CONDITIONAL_OUT": ")"
}
