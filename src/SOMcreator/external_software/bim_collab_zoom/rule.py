import logging
from typing import Callable, Any

from lxml import etree

from . import condition, action
from . import constants as c


def _write_base(attribute_name: str, pset_name: str, value_type: str) -> (etree.Element, etree.Element):
    """Schreibt basisinfos die für jede Attributregel identisch sind"""
    rule = etree.Element(c.RULE)
    etree.SubElement(rule, c.IFCTYPE).text = c.ANY
    xml_property = etree.SubElement(rule, c.PROPERTY)
    etree.SubElement(xml_property, c.NAME).text = attribute_name
    etree.SubElement(xml_property, c.PSETNAME).text = pset_name
    etree.SubElement(xml_property, c.TYPE).text = c.PROPERTYSET
    etree.SubElement(xml_property, c.VALUETYPE).text = value_type
    etree.SubElement(xml_property, c.UNIT).text = c.NONE
    xml_condition = etree.SubElement(rule, c.CONDITION)
    return rule, xml_condition


def _simple_rule(attribute_name: str, property_set_name: str,
                 value: Any, datatype: str, func_condition: Callable, func_action: Callable):
    xml_rule, xml_condition = _write_base(attribute_name, property_set_name, datatype)
    func_condition(xml_condition, value)
    func_action(xml_rule)
    return xml_rule


def add_if_not_existing(attribute_name: str, pset_name: str, data_type: str):
    return [_simple_rule(attribute_name, pset_name, data_type, data_type, condition.is_not_existing,
                         action.add)]


def remove_if_not_in_string_list(attribute_name: str, pset_name: str, value_list) -> list[etree.Element]:
    return [_simple_rule(attribute_name, pset_name, value_list, c.STRING, condition.not_in_list, action.remove)]


def add_if_not_in_string_list(attribute_name: str, pset_name: str, value_list) -> list[etree.Element]:
    return [_simple_rule(attribute_name, pset_name, value_list, c.STRING, condition.not_in_list, action.add)]


def remove_if_in_string_list(attribute_name: str, pset_name: str, value_list) -> list[etree.Element]:
    return [_simple_rule(attribute_name, pset_name, value_list, c.STRING, condition.is_in_list, action.remove)]


def add_if_in_string_list(attribute_name: str, pset_name: str, value_list) -> list[etree.Element]:
    return [_simple_rule(attribute_name, pset_name, value_list, c.STRING, condition.is_in_list, action.add)]


def add_if_outside_of_range(attribute_name: str, pset_name: str, min_value: float, max_value: float):
    r1 = _simple_rule(attribute_name, pset_name, min_value, c.DOUBLE, condition.is_less_than, action.add)
    r2 = _simple_rule(attribute_name, pset_name, max_value, c.DOUBLE, condition.is_greater_than, action.add)
    return [r1, r2]


def add_if_in_range(attribute_name: str, pset_name: str, min_value: float, max_value: float):
    r1 = _simple_rule(attribute_name, pset_name, min_value, c.DOUBLE, condition.is_greater_than, action.and_)
    r2 = _simple_rule(attribute_name, pset_name, max_value, c.DOUBLE, condition.is_less_than, action.add)
    return [r1, r2]


def numeric_list(attribute_name, pset_name, value_list) -> list[etree.Element]:
    """Schreibt Regel die kontrolliert ob ein Zahlenwert in einer Liste aus Zahlen vorkommt"""
    rule_list: list[etree.Element] = list()
    rule_list += add_if_not_existing(attribute_name, pset_name, c.DOUBLE)
    for index, value in enumerate(value_list):
        if index == len(value_list) - 1:
            xml_rule = _simple_rule(attribute_name, pset_name, value, c.DOUBLE, condition.not_equal, action.add)
        else:
            xml_rule = _simple_rule(attribute_name, pset_name, value, c.DOUBLE, condition.not_equal, action.and_)
        rule_list.append(xml_rule)
    return rule_list


def numeric_range( attribute_name, property_set_name,
                  value_range_list: list[tuple[float, float]]) -> list[etree.Element]:
    """Schreibt eine Regel die kontrolliert ob ein Zahlenwert in einem Wertebereich vorkommt"""

    def merge_list(inter, start_index=0):
        for i in range(start_index, len(inter) - 1):
            if inter[i][1] > inter[i + 1][0]:
                new_start = inter[i][0]
                new_end = max(inter[i + 1][1], inter[i][1])
                inter[i] = [new_start, new_end]
                del inter[i + 1]
                return merge_list(inter.copy(), start_index=i)
        return inter

    if not value_range_list:
        logging.error(f"Empty Value list at {property_set_name}:{attribute_name}")
        return list()

    sorted_range_list = sorted([[min(v1, v2), max(v1, v2)] for [v1, v2] in value_range_list])
    sorted_range_list = merge_list(sorted_range_list)

    minimal_value = sorted_range_list[0][0]
    maximal_value = sorted_range_list[-1][1]

    rule_list = list()
    rule_list+= add_if_not_existing(attribute_name,property_set_name,c.DOUBLE)
    rule_list += add_if_outside_of_range(attribute_name, property_set_name, minimal_value, maximal_value)

    for [v1_min, v1_max], [v2_min, v2_max] in zip(sorted_range_list, sorted_range_list[1:]):
        rule_list += add_if_in_range(attribute_name, property_set_name, v1_max, v2_min)
    return rule_list

def remove_if_not_exist(attribute_name: str, property_set_name: str) -> list[etree.Element]:
    return _simple_rule(attribute_name, property_set_name, "", c.STRING, condition.is_not_value, action.remove)
