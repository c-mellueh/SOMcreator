from ...constants import value_constants

STRING = "StringValue"
DOUBLE = "DoubleValue"
BOOL = "BoolValue"
LOGICAL = "LogicalValue"

# String Conditions
ISNOT = "IsNot"
IS = "Is"
CONTAINS = "Contains"
DOESNOTCONTAIN = "DoesNotContain"
STARTSWITH = "StartsWith"
ENDSWITH = "EndsWith"
OR = "Or"
NOR = "Nor"
STRING_DEF = "StringIsDefined"
STRING_UNDEF = "StringIsNotDefined"

# NumberConditions
EQUALS = "Equals"
NOTEQ = "NotEquals"
LESS = "Less"
GREATER = "Greater"
LESSEQUAL = "LessEqual"
GREATEREQUAL = "GreaterEqual"
NUMERIC_DEF = "NumericIsDefined"
NUMERIC_UNDEF = "NumericIsNotDefined"

# BoolConditions
BOOLTRUE = "BooleanTrue"
BOOLFALSE = "BooleanFalse"
BOOL_DEF = "BooleanIsDefined"
BOOL_UNDEF = "BooleanIsNotDefined"

# LogicContions
LOGICTRUE = "LogicalTrue"
LOGICFALSE = "LogicalFalse"
LOGICUNKNOW = "LogicalUnknown"
LOGICAL_DEF = "LogicalIsDefined"
LOGICAL_UNDEF = "LogicalIsNotDefined"

DATATYPE_DICT = {value_constants.XS_STRING: STRING,
                 value_constants.XS_BOOL: BOOL,
                 value_constants.XS_INT: DOUBLE,
                 value_constants.XS_DOUBLE: DOUBLE,
                 value_constants.XS_LONG: DOUBLE}
