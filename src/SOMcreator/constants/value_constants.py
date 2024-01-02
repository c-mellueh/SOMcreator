from .ifc_datatypes import LABEL,REAL,BOOLEAN,DATE,INTEGER
VALUE = "Value"
FORMAT = "Format"
RANGE = "Range"
LIST = "List"
XS_STRING = LABEL
XS_DOUBLE = REAL
XS_BOOL = BOOLEAN
XS_LONG = REAL
DATATYPE_DATE = DATE
DATATYPE_NUMBER = REAL
XS_INT = INTEGER
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