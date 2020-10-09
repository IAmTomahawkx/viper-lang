
class Configuration:
    __slots__ = tuple()
    bracket_code_in     = "{"
    bracket_code_out    = "}"
    bracket_args_in     = "("
    bracket_args_out    = ")"
    bracket_call_in     = "("
    bracket_call_out    = ")"
    bracket_condition_in= "("
    bracket_condition_out= ")"

    keyword_static      = "static"
    keyword_func        = "func"
    keyword_null        = "none"
    keyword_if          = "if"
    keyword_elseif      = "else if"
    keyword_else        = "else"
    keyword_false       = "false"
    keyword_true        = "true"
    keyword_namespace   = "$vars"
    keyword_return      = "return"
    keyword_try         = "do"
    keyword_catch       = "error"
    keyword_throw       = "raise"
    keyword_for         = "foreach"

    keyword_equals      = ("is", "==")
    keyword_not_equals  = ("not", "!=")
    keyword_greater     = (">",)
    keyword_smaller     = ("<",)
    keyword_contains    = ("in",)
    keyword_not_contains= ("!in",)

    reference_marker    = "$"
    comment             = "//"

    boolops = {*keyword_equals, *keyword_not_equals, *keyword_greater, *keyword_smaller, *keyword_contains, *keyword_not_contains}
