from . import constants as c
from lxml import etree

def add(xml_rule) -> etree.Element:
    xml_action = etree.SubElement(xml_rule, c.ACTION)
    etree.SubElement(xml_action, c.TYPE).text = c.ADD
    return xml_action

def and_(xml_rule) -> etree.Element:
    xml_action = etree.SubElement(xml_rule, c.ACTION)
    etree.SubElement(xml_action, c.TYPE).text = c.AND
    return xml_action
#
def remove(xml_rule) -> etree.Element:
    xml_action = etree.SubElement(xml_rule, c.ACTION)
    etree.SubElement(xml_action, c.TYPE).text = c.REMOVE
    return xml_action
#
# def add(xml_rule) -> etree.Element:
#     xml_action = etree.SubElement(xml_rule, c.ACTION)
#     etree.SubElement(xml_action, c.TYPE).text = c.ADD
#     return xml_action