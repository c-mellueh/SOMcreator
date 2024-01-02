VALUE = "Value"
FORMAT = "Format"
RANGE = "Range"
LIST = "List"
XS_STRING = "IfcLabel"
XS_DOUBLE = "IfcReal"
XS_BOOL = "IfcBoolean"
XS_LONG = "IfcReal"
DATATYPE_DATE = "IfcDate"
DATATYPE_NUMBER = "IfcReal"
XS_INT = "IfcInteger"
RANGE_STRINGS = ["Range", "range", "RANGE"]
VALUE_TYPE_LOOKUP = {VALUE: "Value", FORMAT: "Format", RANGE: "Range", LIST: "List",}
AGGREGATION = 1
INHERITANCE = 2
SHARED_PARAMETERS = "SharedParameters"
EXISTS = "Exists"
DATA_TYPES = [XS_STRING,XS_LONG,XS_INT,XS_DOUBLE,XS_BOOL,DATATYPE_DATE]
OLD_DATATYPE_DICT = {"xs:string": XS_STRING,
                     "xs:double": XS_DOUBLE,
                     "xs:boolean": XS_BOOL,
                     "xs:long": XS_LONG,
                     "xs:int": XS_INT}