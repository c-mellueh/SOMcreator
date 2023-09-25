from lxml import etree

from src.SOMcreator import classes
from src.SOMcreator.constants import value_constants
from . import constants as c


def is_value(xml_condition, value: str):
    etree.SubElement(xml_condition, c.TYPE).text = c.IS
    etree.SubElement(xml_condition, c.VALUE).text = value


def is_not_value(xml_condition, value: str):
    etree.SubElement(xml_condition, c.TYPE).text = c.ISNOT
    etree.SubElement(xml_condition, c.VALUE).text = value


def is_not_existing(xml_condition, data_type: str):
    """Schreibt die Condition ob Attribut nicht angelegt ist"""

    if data_type == c.DOUBLE:
        etree.SubElement(xml_condition, c.TYPE).text = c.NUMERIC_UNDEF
    elif data_type == c.BOOL:
        etree.SubElement(xml_condition, c.TYPE).text = c.BOOL_UNDEF
    elif data_type == c.STRING:
        etree.SubElement(xml_condition, c.TYPE).text = c.STRING_UNDEF
    etree.SubElement(xml_condition, c.VALUE)


def is_existing(xml_condition, data_type: str):
    """Schreibt die Condition ob Attribut angelegt ist"""

    if data_type in (value_constants.XS_INT, value_constants.XS_LONG, value_constants.XS_DOUBLE):
        etree.SubElement(xml_condition, c.TYPE).text = c.STRING_DEF
    elif data_type == value_constants.XS_BOOL:
        etree.SubElement(xml_condition, c.TYPE).text = c.BOOL_DEF
    elif data_type == value_constants.XS_STRING:
        etree.SubElement(xml_condition, c.TYPE).text = c.STRING_DEF
    etree.SubElement(xml_condition, c.VALUE)


def is_in_list(xml_condition, value_list):
    """Screibt die Condition ob Attribut einem bestimmten Wert entspricht"""
    etree.SubElement(xml_condition, c.TYPE).text = c.OR
    etree.SubElement(xml_condition, c.VALUE).text = ",".join(value_list)


def not_in_list(xml_condition, value_list):
    """Screibt die Condition ob Attribut einem bestimmten Wert nicht entspricht"""
    etree.SubElement(xml_condition, c.TYPE).text = c.NOR
    etree.SubElement(xml_condition, c.VALUE).text = ",".join(value_list)


def format(xml_condition, attribute: classes.Attribute):
    """Schreibt die Contition ob Attribut einem bestimmten Format entspricht"""
    pass


def range(xml_condition, value: float, gt: bool = True):
    """Schreibt die Condtion ob Attribut in einem gewissen Wertebereich liegt
    gt: Greater Than -> Wenn ja, dann soll Suchwert größer value ansonst Suchwert kleiner value """
    if gt:
        etree.SubElement(xml_condition, c.TYPE).text = "Greater"
    else:
        etree.SubElement(xml_condition, c.TYPE).text = "Less"
    etree.SubElement(xml_condition, c.VALUE).text = str(value)


def not_equal(xml_condition, value):
    etree.SubElement(xml_condition, c.TYPE).text = c.NOTEQ
    etree.SubElement(xml_condition, c.VALUE).text = str(value)


def is_less_than(xml_condition, value):
    etree.SubElement(xml_condition, c.TYPE).text = c.LESS
    etree.SubElement(xml_condition, c.VALUE).text = str(value)
    pass


def is_greater_than(xml_condition, value):
    etree.SubElement(xml_condition, c.TYPE).text = c.GREATER
    etree.SubElement(xml_condition, c.VALUE).text = str(value)
