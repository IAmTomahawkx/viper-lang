VIPER_KEYWORDS = {
    "VIPER_STATIC": "static",
    "VIPER_FUNC": "func",
    "VIPER_NULL": "None",
    
    "VIPER_IF": "if",
    "VIPER_ELIF": "else if",
    "VIPER_ELSE": "else",
    
    "VIPER_FALSE": "false",
    "VIPER_TRUE": "true",
    
    "VIPER_NAMESPACE": "$namespace",
    "VIPER_RETURN": "return",
    
    "VIPER_EQUALS": ["is", "=="],
    "VIPER_NOT_EQUALS": ["is not", "!="],
    "VIPER_GREATER": ">",
    "VIPER_SMALLER": "<",
    "VIPER_CONTAINS": "in",
    "VIPER_NOTCONTAINS": "!in",
    
    "VIPER_VARMARKER": "$",
    
    "VIPER_COMMENT": "//",

    "VIPER_TRY": "try",
    "VIPER_CATCH": "error",
    "VIPER_THROW": "raise"
}

# don't touch this one
VIPER_STRICT_PARSING_KEYWORDS = [
    VIPER_KEYWORDS['VIPER_FUNC'],
    VIPER_KEYWORDS['VIPER_STATIC'],
    VIPER_KEYWORDS['VIPER_RETURN']
]

VIPER_BRACKETS = {
    "VIPER_CODE_IN": "{",
    "VIPER_CODE_OUT": "}",
    "VIPER_FUNCTIONARGS_IN": "(",
    "VIPER_FUNCTIONARGS_OUT": ")",
    "VIPER_FUNCTIONCALL_IN": "(",
    "VIPER_FUNCTIONCALL_OUT": ")",
    "VIPER_CONDITIONAL_IN": "(",
    "VIPER_CONDITIONAL_OUT": ")"
}
