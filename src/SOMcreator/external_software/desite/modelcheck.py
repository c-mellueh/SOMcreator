from __future__ import annotations

import codecs
import os
import uuid
from xml.etree.ElementTree import Element

import jinja2
from anytree import AnyNode
from lxml import etree

from constants import json_constants
from src.SOMcreator import classes, constants, Template
from .desite import handle_header, output_date_time


def add_js_rule(parent: Element, file: codecs.StreamReaderWriter) -> str | None:
    name = os.path.basename(file.name)
    if not name.endswith(".js"):
        return None
    else:
        rule_script = etree.SubElement(parent, "ruleScript")

        name = name.split("_")[1:]
        name = "_".join(name)
        rule_script.set("name", name[:-3])
        rule_script.set("active", "true")
        rule_script.set("resume", "false")

        code = etree.SubElement(rule_script, "code")
        file = file.read()

        code.text = file
        code.text = etree.CDATA(code.text)

    return file


def handle_element_section(xml_qa_export: Element) -> Element:
    xml_element_section = etree.SubElement(xml_qa_export, "elementSection")
    return xml_element_section


def handle_container(xml_element_section: Element, text) -> Element:
    container = etree.SubElement(xml_element_section, "container")
    container.set("ID", str(uuid.uuid4()))
    container.set("name", text)
    return container


def handle_checkrun(xml_container: Element, name: str, author: str = "DesiteRuleCreator") -> Element:
    checkrun = etree.SubElement(xml_container, "checkrun")
    _uuid = str(uuid.uuid4())
    checkrun.set("ID", _uuid)
    checkrun.set("name", name)
    checkrun.set("active", "true")
    checkrun.set("user", str(author))
    checkrun.set("date", str(output_date_time))
    checkrun.set("state", "0")
    checkrun.set("objectsOnly", "1")
    checkrun.set("partsOfComposites", "0")
    checkrun.set("createFailed", "true")
    checkrun.set("createWarnings", "true")
    checkrun.set("createIgnored", "false")
    checkrun.set("createPassed", "true")
    checkrun.set("createUndefined", "false")
    return checkrun


def init_xml(project: classes.Project) -> (Element, Element):
    xml_qa_export = handle_header(project, "qaExport")
    xml_element_section = handle_element_section(xml_qa_export)
    text = f"{project.name} : {project.version}"
    xml_container = handle_container(xml_element_section, text)
    return xml_container, xml_qa_export


def handle_rule(xml_checkrun: Element, rule_type: str) -> Element:
    rule = etree.SubElement(xml_checkrun, "rule")
    rule.set("type", rule_type)
    if rule_type == "UniquePattern":
        etree.SubElement(rule, "patternList")
        code = etree.SubElement(xml_checkrun, "code")
        code.text = ""

    return rule


def handle_attribute_rule_list(xml_rule: Element) -> Element:
    attribute_rule_list = etree.SubElement(xml_rule, "attributeRuleList")
    return attribute_rule_list


def handle_template() -> jinja2.Template:
    file_loader = jinja2.FileSystemLoader(Template.HOME_DIR)
    env = jinja2.Environment(loader=file_loader)
    env.trim_blocks = True
    env.lstrip_blocks = True
    template = env.get_template(constants.TEMPLATE_NAME)
    return template


def define_xml_elements(project: classes.Project, xml_container: Element, name: str) -> (Element, Element):
    xml_checkrun = handle_checkrun(xml_container, name=name, author=project.author)
    xml_rule = handle_rule(xml_checkrun, "Attributes")
    xml_attribute_rule_list = handle_attribute_rule_list(xml_rule)
    handle_rule(xml_checkrun, "UniquePattern")

    return xml_checkrun, xml_attribute_rule_list


def handle_js_rules(xml_attribute_rule_list: Element, starts_with: str) -> None:
    folder = os.path.join(Template.HOME_DIR, constants.FILEPATH_JS)

    for fn in os.listdir(folder):
        if fn.startswith(starts_with):
            file = codecs.open(f"{folder}/{fn}", encoding="utf-8")
            add_js_rule(xml_attribute_rule_list, file)


def handle_rule_script(xml_attribute_rule_list: Element, name: str) -> Element:
    rule_script = etree.SubElement(xml_attribute_rule_list, "ruleScript")
    rule_script.set("name", name)
    rule_script.set("active", "true")
    rule_script.set("resume", "true")
    return rule_script


def handle_code(xml_rule_script: Element) -> Element:
    code = etree.SubElement(xml_rule_script, "code")
    return code


def handle_object_rules(project: classes.Project, project_tree, base_xml_container: Element,
                        template: jinja2.Template) -> dict[
    Element, classes.Object]:
    def handle_tree_structure(parent_xml_container, parent_node: AnyNode) -> None:

        def create_container(xml_container, node: AnyNode):
            new_xml_container = handle_container(xml_container, node.obj.name)
            create_object(new_xml_container, node)
            for child_node in sorted(node.children, key=lambda x: x.id):
                handle_tree_structure(new_xml_container, child_node)

        def create_object(xml_container, node: AnyNode):
            obj: classes.Object = node.obj
            if obj.ident_attrib is None:
                return
            xml_checkrun = handle_checkrun(xml_container, obj.name, project.author)
            xml_rule = handle_rule(xml_checkrun, "Attributes")
            xml_attribute_rule_list = handle_attribute_rule_list(xml_rule)
            xml_rule_script = handle_rule_script(xml_attribute_rule_list, name=obj.name)
            xml_code = handle_code(xml_rule_script)

            property_sets = [pset for pset in obj.property_sets if
                             len(pset.attributes) > 0]

            ident_name = obj.ident_attrib.name
            ident_property_set = obj.ident_attrib.property_set.name
            if ident_property_set == json_constants.IGNORE_PSET:
                ident_property_set = ""
            else:
                ident_property_set = f"{ident_property_set}:"

            cdata_code = template.render(psets=property_sets, object=obj, ident=ident_name,
                                         ident_pset=ident_property_set, constants=constants)
            xml_code.text = cdata_code
            handle_rule(xml_checkrun, "UniquePattern")

            xml_object_dict[xml_checkrun] = obj

        if parent_node.children:
            create_container(parent_xml_container, parent_node)
        else:
            create_object(parent_xml_container, parent_node)

    xml_object_dict: dict[Element, classes.Object] = dict()
    root_nodes = project_tree.children

    for root_node in sorted(root_nodes, key=lambda x: x.id):
        handle_tree_structure(base_xml_container, root_node)
    return xml_object_dict


def handle_data_section(xml_qa_export: Element, xml_checkrun_first: Element,
                        xml_checkrun_obj: dict[Element, classes.Object],
                        xml_checkrun_last: Element) -> None:
    def get_name() -> str:
        """Transorms native IFC Attributes like IfcType into desite Attributes"""

        pset_name = obj.ident_attrib.property_set.name
        if pset_name == "IFC":
            return obj.ident_attrib.name

        else:
            return f"{pset_name}:{obj.ident_attrib.name}"

    xml_data_section = etree.SubElement(xml_qa_export, "dataSection")

    check_run_data = etree.SubElement(xml_data_section, "checkRunData")
    check_run_data.set("refID", str(xml_checkrun_first.attrib.get("ID")))
    etree.SubElement(check_run_data, "checkSet")

    for xml_checkrun, obj in xml_checkrun_obj.items():
        check_run_data = etree.SubElement(xml_data_section, "checkRunData")
        check_run_data.set("refID", str(xml_checkrun.attrib.get("ID")))
        filter_list = etree.SubElement(check_run_data, "filterList")
        xml_filter = etree.SubElement(filter_list, "filter")

        xml_filter.set("name", get_name())
        xml_filter.set("dt", "xs:string")
        pattern = f'"{obj.ident_attrib.value[0]}"'  # ToDO: ändern
        xml_filter.set("pattern", pattern)

    check_run_data = etree.SubElement(xml_data_section, "checkRunData")
    check_run_data.set("refID", str(xml_checkrun_last.attrib.get("ID")))
    filter_list = etree.SubElement(check_run_data, "filterList")
    xml_filter = etree.SubElement(filter_list, "filter")
    xml_filter.set("name", "Check_State")
    xml_filter.set("dt", "xs:string")
    xml_filter.set("pattern", '"Ungeprüft"')


def handle_property_section(xml_qa_export: Element) -> None:
    repository = etree.SubElement(xml_qa_export, "repository")
    property_type_section = etree.SubElement(repository, "propertyTypeSection")
    ptype = etree.SubElement(property_type_section, "ptype")

    ptype.set("key", "1")
    ptype.set("name", "Bestandsdaten:Objekttyp")
    ptype.set("datatype", "xs:string")
    ptype.set("unit", "")
    ptype.set("inh", "true")

    property_section = etree.SubElement(repository, "propertySection")


def export_json(project: classes.Project, path: str, project_tree=None) -> None:
    def export() -> None:
        template = handle_template()
        xml_container, xml_qa_export = init_xml(project)
        xml_checkrun_first, xml_attribute_rule_list = define_xml_elements(project, xml_container, "initial_tests")
        handle_js_rules(xml_attribute_rule_list, "start")
        xml_checkrun_obj = handle_object_rules(project, project_tree, xml_container, template)
        xml_checkrun_last, xml_attribute_rule_list = define_xml_elements(project, xml_container, "untested")
        handle_js_rules(xml_attribute_rule_list, "end")
        handle_data_section(xml_qa_export, xml_checkrun_first, xml_checkrun_obj, xml_checkrun_last)
        handle_property_section(xml_qa_export)

        tree = etree.ElementTree(xml_qa_export)
        with open(path, "wb") as f:
            tree.write(f, xml_declaration=True, pretty_print=True, encoding="utf-8", method="xml")

    if project_tree is None:
        project_tree = project.tree()
    export()


def export_csv(project, path):
    pass
