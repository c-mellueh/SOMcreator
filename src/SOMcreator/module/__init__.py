from .ifctosql import IfcToSQLProperties
from .parsesql import ParseSQLProperties
import SOMcreator

SOMcreator.ParseSQLProperties = ParseSQLProperties()
SOMcreator.IfcToSQLProperties = IfcToSQLProperties()
