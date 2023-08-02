from __future__ import annotations

import codecs
import csv
import datetime
import json
import os
import uuid
import xml.etree.ElementTree as ET

import jinja2
from anytree import AnyNode
from lxml import etree

from .. import classes, constants, Template
from ..Template import HOME_DIR,BOOKMARK_TEMPLATE
output_date_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
output_date = datetime.datetime.now().strftime("%Y-%m-%d")


def handle_header(project: classes.Project, export_format: str) -> etree._Element:
    ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    xml_header = etree.Element(f'{{http://www.w3.org/2001/XMLSchema-instance}}{export_format}')
    xml_header.set("user", str(project.author))
    xml_header.set("date", str(output_date_time))
    xml_header.set("version", "3.0.1")  # TODO: Desite version hinzufügen
    return xml_header


##TODO add xs:bool

def export_modelcheck(project, path: str, project_tree=None) -> None:
    def add_js_rule(parent: etree._Element, file: codecs.StreamReaderWriter) -> str | None:
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

    def handle_element_section(xml_qa_export: etree._Element) -> etree._Element:
        xml_element_section = etree.SubElement(xml_qa_export, "elementSection")
        return xml_element_section

    def handle_container(xml_element_section: etree._Element, text) -> etree._Element:
        container = etree.SubElement(xml_element_section, "container")
        container.set("ID", str(uuid.uuid4()))
        container.set("name", text)
        return container

    def handle_checkrun(xml_container: etree._Element, name: str, author: str = "DesiteRuleCreator") -> etree._Element:
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

    def init_xml(project) -> (etree._Element, etree._Element):
        xml_qa_export = handle_header(project, "qaExport")
        xml_element_section = handle_element_section(xml_qa_export)
        text = f"{project.name} : {project.version}"
        xml_container = handle_container(xml_element_section, text)
        return xml_container, xml_qa_export

    def handle_rule(xml_checkrun: etree._Element, rule_type: str) -> etree._Element:
        rule = etree.SubElement(xml_checkrun, "rule")
        rule.set("type", rule_type)
        if rule_type == "UniquePattern":
            etree.SubElement(rule, "patternList")
            code = etree.SubElement(xml_checkrun, "code")
            code.text = ""

        return rule

    def handle_attribute_rule_list(xml_rule: etree._Element) -> etree._Element:
        attribute_rule_list = etree.SubElement(xml_rule, "attributeRuleList")
        return attribute_rule_list

    def handle_template() -> jinja2.Template:
        path = Template.HOME_DIR
        file_loader = jinja2.FileSystemLoader(path)
        env = jinja2.Environment(loader=file_loader)
        env.trim_blocks = True
        env.lstrip_blocks = True
        template = env.get_template("template.txt")

        return template

    def define_xml_elements(xml_container: etree._Element, name: str) -> (etree._Element, etree._Element):
        xml_checkrun = handle_checkrun(xml_container, name=name, author=project.author)
        xml_rule = handle_rule(xml_checkrun, "Attributes")
        xml_attribute_rule_list = handle_attribute_rule_list(xml_rule)
        handle_rule(xml_checkrun, "UniquePattern")

        return xml_checkrun, xml_attribute_rule_list

    def handle_js_rules(xml_attribute_rule_list: etree._Element, starts_with: str) -> None:
        folder = os.path.join(Template.HOME_DIR, constants.FILEPATH_JS)

        for fn in os.listdir(folder):
            if fn.startswith(starts_with):
                file = codecs.open(f"{folder}/{fn}", encoding="utf-8")
                add_js_rule(xml_attribute_rule_list, file)

    def handle_rule_script(xml_attribute_rule_list: etree._Element, name: str) -> etree._Element:
        rule_script = etree.SubElement(xml_attribute_rule_list, "ruleScript")
        rule_script.set("name", name)
        rule_script.set("active", "true")
        rule_script.set("resume", "true")
        return rule_script

    def handle_code(xml_rule_script: etree._Element) -> etree._Element:
        code = etree.SubElement(xml_rule_script, "code")
        return code

    def handle_object_rules(base_xml_container: etree._Element, template: jinja2.Template) -> dict[
        etree._Element, classes.Object]:

        def handle_tree_structure(parent_xml_container, parent_node: AnyNode) -> None:

            def create_container(xml_container, node: AnyNode):
                new_xml_container = handle_container(xml_container, node.obj.name)
                create_object(new_xml_container, node)
                for child_node in sorted(node.children, key=lambda x: x.id):
                    handle_tree_structure(new_xml_container, child_node)

            def create_object(xml_container, node: AnyNode):
                obj: classes.Object = node.obj
                xml_checkrun = handle_checkrun(xml_container, obj.name, project.author)
                xml_rule = handle_rule(xml_checkrun, "Attributes")
                xml_attribute_rule_list = handle_attribute_rule_list(xml_rule)
                xml_rule_script = handle_rule_script(xml_attribute_rule_list, name=obj.name)
                xml_code = handle_code(xml_rule_script)

                property_sets = [pset for pset in obj.property_sets if len(pset.attributes) > 0]
                ident_name = obj.ident_attrib.name
                ident_property_set = obj.ident_attrib.property_set.name
                if ident_property_set == constants.IGNORE_PSET:
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

        xml_object_dict: dict[etree._Element, classes.Object] = dict()
        root_nodes = project_tree.children

        for root_node in sorted(root_nodes, key=lambda x: x.id):
            handle_tree_structure(base_xml_container, root_node)
        return xml_object_dict

    def handle_data_section(xml_qa_export: etree._Element, xml_checkrun_first: etree._Element,
                            xml_checkrun_obj: dict[etree._Element, classes.Object],
                            xml_checkrun_last: etree._Element) -> None:
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

    def handle_property_section(xml_qa_export: etree._Element) -> None:
        repository = etree.SubElement(xml_qa_export, "repository")
        property_type_section = etree.SubElement(repository, "propertyTypeSection")
        ptype = etree.SubElement(property_type_section, "ptype")

        ptype.set("key", "1")
        ptype.set("name", "Bestandsdaten:Objekttyp")
        ptype.set("datatype", "xs:string")
        ptype.set("unit", "")
        ptype.set("inh", "true")

        property_section = etree.SubElement(repository, "propertySection")

    def export(path: str) -> None:

        template = handle_template()
        xml_container, xml_qa_export = init_xml(project)
        xml_checkrun_first, xml_attribute_rule_list = define_xml_elements(xml_container, "initial_tests")
        handle_js_rules(xml_attribute_rule_list, "start")
        xml_checkrun_obj = handle_object_rules(xml_container, template)
        xml_checkrun_last, xml_attribute_rule_list = define_xml_elements(xml_container, "untested")
        handle_js_rules(xml_attribute_rule_list, "end")
        handle_data_section(xml_qa_export, xml_checkrun_first, xml_checkrun_obj, xml_checkrun_last)
        handle_property_section(xml_qa_export)

        tree = etree.ElementTree(xml_qa_export)
        with open(path, "wb") as f:
            tree.write(f, xml_declaration=True, pretty_print=True, encoding="utf-8", method="xml")

    if project_tree is None:
        project_tree = project.tree()
    export(path)


def export_bs(project: classes.Project, path: str) -> None:
    def handle_elementsection(xml_parent: etree._Element):

        def handle_section(aggregation: classes.Aggregation, xml_item: etree._Element) -> None:

            nonlocal id_dict
            xml_child = etree.SubElement(xml_item, "section")
            id_dict[aggregation] = aggregation.uuid
            xml_child.set("ID", aggregation.uuid)
            xml_child.set("name", aggregation.object.name)
            xml_child.set("pre", "")
            xml_child.set("type", "typeBsGroup")
            xml_child.set("takt", "")

            for child in sorted(aggregation.children, key=lambda x: x.name):
                connection_type = aggregation.connection_dict[child]
                if connection_type == constants.AGGREGATION:
                    handle_section(child, xml_child)
                else:
                    handle_section(child, xml_item)

        xml_elementsection = etree.SubElement(xml_parent, "elementSection")
        xml_root = etree.SubElement(xml_elementsection, "section")
        xml_root.set("ID", str(uuid.uuid4()))
        xml_root.set("name", "BS Autogenerated")
        xml_root.set("pre", "")
        xml_root.set("type", "typeBsContainer")
        xml_root.set("takt", "")

        root_objects: list[classes.Aggregation] = [aggreg for aggreg in classes.Aggregation if
                                                   aggreg.is_root]

        root_objects.sort(key=lambda x: x.name)

        id_dict = dict()
        for aggreg in root_objects:
            handle_section(aggreg, xml_root)

        return xml_elementsection, id_dict

    def handle_repository(xml_parent: etree._Element, id_dict: dict[classes.Aggregation, str]) -> None:
        def handle_property_type_section() -> dict[str, int]:
            xml_property_type_section = etree.SubElement(xml_repo, "propertyTypeSection")

            attribute_dict = dict()

            i = 1
            for attribute in classes.Attribute:
                # use attribute_text instead of attribute to remove duplicates
                attribute_text = f"{attribute.property_set.name}:{attribute.name}"
                if attribute_text not in attribute_dict:
                    xml_ptype = etree.SubElement(xml_property_type_section, "ptype")
                    xml_ptype.set("key", str(i))
                    xml_ptype.set("name", attribute_text)
                    xml_ptype.set("datatype", attribute.data_type)
                    xml_ptype.set("unit", "")
                    xml_ptype.set("inh", "false")
                    attribute_dict[attribute_text] = i
                    i += 1

            return attribute_dict

        def handle_property_section() -> None:
            xml_property_section = etree.SubElement(xml_repo, "propertySection")

            for node, ref_id in id_dict.items():
                obj = node.object
                for property_set in obj.property_sets:
                    for attribute in property_set.attributes:
                        attribute_text = f"{attribute.property_set.name}:{attribute.name}"
                        ref_type = attribute_dict[attribute_text]
                        xml_property = etree.SubElement(xml_property_section, "property")
                        xml_property.set("refID", str(ref_id))
                        xml_property.set("refType", str(ref_type))
                        if attribute == obj.ident_attrib:
                            xml_property.text = attribute.value[0]
                        else:
                            xml_property.text = "füllen!"

        xml_repo = etree.SubElement(xml_parent, "repository")
        xml_id_mapping = etree.SubElement(xml_repo, "IDMapping")

        for i, (item, id_value) in enumerate(id_dict.items()):
            xml_id = etree.SubElement(xml_id_mapping, "ID")
            xml_id.set("k", str(i + 1))
            xml_id.set("v", str(id_value))

        attribute_dict = handle_property_type_section()
        handle_property_section()

    def handle_relation_section(xml_parent: etree._Element) -> None:
        xml_relation_section = etree.SubElement(xml_parent, "relationSection")

        xml_id_mapping = etree.SubElement(xml_relation_section, "IDMapping")
        xml_relation = etree.SubElement(xml_relation_section, "relation")
        xml_relation.set("name", "default")

    def export() -> None:
        xml_boq_export = handle_header(project, "bsExport")
        xml_elementsection, id_dict = handle_elementsection(xml_boq_export)

        xml_link_section = etree.SubElement(xml_boq_export, "linkSection")
        xml_repository = handle_repository(xml_boq_export, id_dict)
        handle_relation_section(xml_boq_export)

        tree = etree.ElementTree(xml_boq_export)

        with open(path, "wb") as f:
            tree.write(f, xml_declaration=True, pretty_print=True, encoding="utf-8", method="xml")

    if path:
        export()
        pass


def export_bookmarks(proj:classes.Project,path: str) -> None:
    def handle_bookmark_list() -> etree.ElementTree:
        xml_bookmarks = etree.Element("bookmarks")
        xml_bookmarks.set("xmlnsxsi", "http://www.w3.org/2001/XMLSchema-instance")
        xml_bookmark_list = etree.SubElement(xml_bookmarks, "cBookmarkList")

        obj: classes.Object
        for obj in sorted(proj.objects, key=lambda x: x.ident_attrib.value[0]):
            xml_bookmark = etree.SubElement(xml_bookmark_list, "cBookmark")
            xml_bookmark.set("ID", str(obj.uuid))

            if isinstance(obj.ident_attrib, classes.Attribute):
                xml_bookmark.set("name", str(obj.ident_attrib.value[0]))

            xml_bookmark.set("bkmType", "2")
            xml_col = etree.SubElement(xml_bookmark, "col")
            xml_col.set("v", "Type##xs:string")

            attribute = obj.ident_attrib
            xml_col = etree.SubElement(xml_bookmark, "col")
            text = f"{attribute.property_set.name}:{attribute.name}##{attribute.data_type}"
            xml_col.set("v", text)

            for property_set in obj.property_sets:
                for attribute in property_set.attributes:
                    if attribute != obj.ident_attrib:
                        xml_col = etree.SubElement(xml_bookmark, "col")
                        text = f"{property_set.name}:{attribute.name}##{attribute.data_type}"
                        xml_col.set("v", text)
        return etree.ElementTree(xml_bookmarks)

    def get_attribute_dict() -> dict[str,str]:
        attribute_dict = {}
        for obj in proj.objects:
            for property_set in obj.property_sets:
                for attribute in property_set.attributes:
                    attribute_dict[f"{property_set.name}:{attribute.name}"] = attribute.data_type

        return attribute_dict
    if not os.path.isdir(path):
        return


    with open(os.path.join(path, "bookmarks.bkxml"), "wb") as f:
        tree = handle_bookmark_list()
        tree.write(f, xml_declaration=True, pretty_print=True, encoding="utf-8", method="xml")

    attrib_dict = get_attribute_dict()
    file_loader = jinja2.FileSystemLoader(HOME_DIR)
    env = jinja2.Environment(loader=file_loader)
    env.trim_blocks = True
    env.lstrip_blocks = True
    template = env.get_template(BOOKMARK_TEMPLATE)
    code = template.render(attribute_dict=attrib_dict)
    with open(os.path.join(path, "bookmark_script.js"), "w") as f:
        f.write(code)


def export_boq(path: str, pset_name):
    def get_distinct_attributes(property_sets: list[classes.PropertySet]):
        attribute_names = list()

        for property_set in property_sets:
            attribute: classes.Attribute
            attribute_names += [attribute.name for attribute in property_set.attributes]

        distinct_attribute_names = list(dict.fromkeys(attribute_names))

        return distinct_attribute_names

    if path:
        with open(path, "w", ) as file:
            writer = csv.writer(file, delimiter=";")
            property_sets = [property_set for property_set in classes.PropertySet if
                             property_set.name == pset_name]
            distinct_attribute_names = get_distinct_attributes(property_sets)
            header = ["Ident", "Object"] + [f"{pset_name}:{name}" for name in distinct_attribute_names]
            writer.writerow(header)
            obj: classes.Object

            objects = [obj for obj in classes.Object if
                       pset_name in [pset.name for pset in obj.property_sets]]  # find objects with matching propertyset
            for obj in objects:
                property_set = obj.get_property_set_by_name(pset_name)
                ident = obj.ident_attrib
                line = [f"{ident.property_set.name}:{ident.name}", ident.value[0]]
                for attribute_name in distinct_attribute_names:
                    attribute: classes.Attribute = property_set.get_attribute_by_name(attribute_name)

                    if attribute is not None:
                        line.append("|".join(attribute.value))
                    else:
                        line.append("")
                writer.writerow(line)

    pass


def export_attribute_json(project: classes.Project, path):
    with open(path, "w") as file:
        json_dict = dict()
        for obj in sorted(project.objects, key=lambda x: x.ident_value):
            if not obj.property_sets:
                continue
            if obj.ident_value is None:
                continue
            json_dict[obj.ident_value] = dict()
            obj_dict = json_dict[obj.ident_value]
            for property_set in obj.property_sets:
                if not property_set.attributes:
                    continue
                obj_dict[property_set.name] = dict()
                pset_dict = obj_dict[property_set.name]
                for attribute in property_set.attributes:
                    pset_dict[attribute.name] = dict()
                    attribute_dict = pset_dict[attribute.name]

                    attribute_dict[constants.DATA_TYPE] = attribute.data_type
                    if not attribute.value:
                        attribute_dict[constants.VALUE_TYPE] = "Exists"
                    else:
                        attribute_dict[constants.VALUE_TYPE] = attribute.value_type
                    attribute_dict[constants.VALUE] = attribute.value
        json.dump(json_dict, file, indent=1)
