from __future__ import annotations
from typing import  Type
from . import constants, classes
from lxml import  etree

def string_to_bool(text: str) -> bool | None:
    if text == str(True):
        return True
    elif text == str(False):
        return False
    else:
        return None

def build_xml(project: classes.Project) -> etree.ElementTree:
    def add_parent(xml_item:etree.Element, item: classes.Object | classes.PropertySet | classes.Attribute) -> None:
        if item.parent is not None:
            xml_item.set(constants.PARENT, str(item.parent.identifier))
        else:
            xml_item.set(constants.PARENT, constants.NONE)

    def add_predefined_property_sets() -> None:
        xml_grouping = etree.SubElement(xml_project, constants.PREDEFINED_PSETS)
        predefined_psets = [pset for pset in classes.PropertySet if pset.object == None]
        for predefined_pset in predefined_psets:
            add_property_set(predefined_pset,xml_grouping)

    def add_objects() -> None:

        def add_object(obj: classes.Object, xml_parent) -> None:
            def add_ifc_mapping():
                xml_ifc_mappings = etree.SubElement(xml_object, constants.IFC_MAPPINGS)
                for mapping in obj.ifc_mapping:
                    xml_ifc_mapping = etree.SubElement(xml_ifc_mappings, constants.IFC_MAPPING)
                    xml_ifc_mapping.text = mapping
                pass

            xml_object = etree.SubElement(xml_parent, constants.OBJECT)
            xml_object.set(constants.NAME, obj.name)
            xml_object.set(constants.IDENTIFIER, str(obj.identifier))
            xml_object.set("is_concept", str(obj.is_concept))
            add_parent(xml_object, obj)

            add_ifc_mapping()
            xml_property_sets = etree.SubElement(xml_object, constants.PROPERTY_SETS)
            for property_set in obj.property_sets:
                add_property_set(property_set, xml_property_sets)

            xml_scripts = etree.SubElement(xml_object, constants.SCRIPTS)
            for script in obj.scripts:
                script: classes.Script = script
                xml_script = etree.SubElement(xml_scripts, constants.SCRIPT)
                xml_script.set(constants.NAME, script.name)
                xml_script.text = script.code

        xml_grouping = etree.SubElement(xml_project, constants.OBJECTS)
        for obj in sorted(classes.Object, key=lambda x:x.name):
            add_object(obj,xml_grouping)

    def add_property_set(property_set: classes.PropertySet, xml_parent:etree.Element) -> None:
        def add_attribute(attribute: classes.Attribute, xml_pset: etree._Element) -> None:
            def add_value(attribute: classes.Attribute, xml_attribute: etree._Element) -> None:
                values = attribute.value
                for value in values:
                    xml_value = etree.SubElement(xml_attribute, "Value")
                    if attribute.value_type == constants.RANGE:
                        xml_from = etree.SubElement(xml_value, "From")
                        xml_to = etree.SubElement(xml_value, "To")
                        xml_from.text = str(value[0])
                        if len(value) > 1:
                            xml_to.text = str(value[1])
                    else:
                        xml_value.text = str(value)

            xml_attribute = etree.SubElement(xml_pset, constants.ATTRIBUTE)
            xml_attribute.set(constants.NAME, attribute.name)
            xml_attribute.set(constants.DATA_TYPE, attribute.data_type)
            xml_attribute.set(constants.VALUE_TYPE, attribute.value_type)
            xml_attribute.set(constants.IDENTIFIER, str(attribute.identifier))
            xml_attribute.set(constants.CHILD_INHERITS_VALUE, str(attribute.child_inherits_values))
            xml_attribute.set(constants.REVIT_MAPPING, str(attribute.revit_name))
            add_parent(xml_attribute, attribute)
            obj = attribute.property_set.object
            if obj is not None and attribute == obj.ident_attrib:
                ident = True
            else:
                ident = False

            xml_attribute.set(constants.IS_IDENTIFIER, str(ident))
            add_value(attribute, xml_attribute)

        xml_pset = etree.SubElement(xml_parent, constants.PROPERTY_SET)
        xml_pset.set(constants.NAME, property_set.name)
        xml_pset.set(constants.IDENTIFIER, str(property_set.identifier))
        add_parent(xml_pset, property_set)

        xml_attributes = etree.SubElement(xml_pset, constants.ATTRIBUTES)
        for attribute in property_set.attributes:
            add_attribute(attribute, xml_attributes)

    def add_aggregation(aggregation: classes.Aggregation, xml_nodes:etree.Element) -> None:
        xml_aggregation = etree.SubElement(xml_nodes, constants.NODE)
        xml_aggregation.set(constants.IDENTIFIER, str(aggregation.uuid))
        xml_aggregation.set(constants.OBJECT.lower(), str(aggregation.object.identifier))
        if aggregation.parent is not None:
            xml_aggregation.set(constants.PARENT, str(aggregation.parent.uuid))
        else:
            xml_aggregation.set(constants.PARENT, constants.NONE)
        xml_aggregation.set(constants.IS_ROOT, str(aggregation.is_root))
        if aggregation .parent is not None:
            xml_aggregation.set(constants.CONNECTION, str(aggregation.parent_connection))
        else:
            xml_aggregation.set(constants.CONNECTION, constants.NONE)

    xml_project = etree.Element(constants.PROJECT)
    xml_project.set(constants.NAME, str(project.name))
    xml_project.set(constants.VERSION, str(project.version))
    xml_project.set(constants.AUTHOR, str(project.author))

    add_predefined_property_sets()
    add_objects()

    xml_nodes = etree.SubElement(xml_project, constants.NODES)

    for aggregation in classes.Aggregation:
        add_aggregation(aggregation,xml_nodes)

    tree = etree.ElementTree(xml_project)
    project.reset_changed()
    return tree

def read_xml(project: classes.Project, path: str = False) -> None:
    if not path:
        return
    tree = etree.parse(path)
    projekt_xml = tree.getroot()
    project.author = projekt_xml.attrib.get(constants.AUTHOR)
    project.name = projekt_xml.attrib.get("name")
    project.version = projekt_xml.attrib.get("version")

    def import_property_sets(xml_property_sets: list[etree._Element]) -> (list[classes.PropertySet], classes.Attribute):

        def import_attributes(xml_attributes: etree._Element,
                              property_set: classes.PropertySet) -> classes.Attribute | None:

            def transform_new_values(xml_attribute: etree._Element) -> list[str]:
                def empty_text(xml_value):
                    if xml_value.text is None:
                        return ""
                    else:
                        return xml_value.text

                value_type = xml_attribute.attrib.get("value_type")
                value = list()

                if value_type != constants.RANGE:
                    for xml_value in xml_attribute:
                        value.append(empty_text(xml_value))

                else:
                    for xml_range in xml_attribute:
                        from_to_list = list()
                        for xml_value in xml_range:
                            if xml_value.tag == "From":
                                from_to_list.append(empty_text(xml_value))
                            if xml_value.tag == "To":
                                from_to_list.append(empty_text(xml_value))
                        value.append(from_to_list)
                return value

            ident_attrib = None

            for xml_attribute in xml_attributes:
                attribs = xml_attribute.attrib
                name = attribs.get(constants.NAME)
                identifier = attribs.get(constants.IDENTIFIER)
                data_type = attribs.get(constants.DATA_TYPE)
                value_type = attribs.get(constants.VALUE_TYPE)
                is_identifier = attribs.get(constants.IS_IDENTIFIER)
                child_inh = string_to_bool(attribs.get(constants.CHILD_INHERITS_VALUE))
                value = transform_new_values(xml_attribute)
                attrib = classes.Attribute(property_set, name, value, value_type, data_type, child_inh, identifier)
                revit_mapping = attribs.get(constants.REVIT_MAPPING)
                attrib.revit_name = revit_mapping
                if is_identifier == str(True):
                    ident_attrib = attrib
            return ident_attrib

        property_sets: list[classes.PropertySet] = list()
        ident_attrib = None

        for xml_property_set in xml_property_sets:
            attribs = xml_property_set.attrib
            name = attribs.get(constants.NAME)
            identifier = attribs.get(constants.IDENTIFIER)
            property_set = classes.PropertySet(name, obj=None, identifier=identifier)

            xml_attrib_group = xml_property_set.find(constants.ATTRIBUTES)
            ident_value = import_attributes(xml_attrib_group, property_set)
            if ident_value is not None:
                ident_attrib = ident_value
            property_sets.append(property_set)

        return property_sets, ident_attrib

    def import_objects(xml_objects:list[etree._Element]):

        def get_obj_data(xml_object: etree._Element) -> (str, str, str, bool):

            name: str = xml_object.attrib.get(constants.NAME)
            parent: str = xml_object.attrib.get(constants.PARENT)
            identifier: str = xml_object.attrib.get(constants.IDENTIFIER)
            is_concept: str = xml_object.attrib.get(constants.IS_CONCEPT)

            return name, parent, identifier, string_to_bool(is_concept)

        def import_scripts(xml_scripts: etree._Element | None, obj: classes.Object) -> None:
            if xml_scripts is None:
                return
            for xml_script in xml_scripts:
                name = xml_script.attrib.get("name")
                code = xml_script.text
                script = classes.Script(name, obj)
                script.code = code

        for xml_object in xml_objects:
            xml_property_group = xml_object.find(constants.PROPERTY_SETS)
            xml_script_group = xml_object.find(constants.SCRIPTS)
            xml_mapping_group = xml_object.find(constants.IFC_MAPPINGS)

            property_sets, ident_attrib = import_property_sets(xml_property_group)
            name, parent, identifer, is_concept = get_obj_data(xml_object)
            obj = classes.Object(name, ident_attrib, identifier=identifer)
            ident_dict[identifer] = obj

            obj.ifc_mapping = [mapping.text for mapping in xml_mapping_group]

            for property_set in property_sets:
                obj.add_property_set(property_set)

            import_scripts(xml_script_group, obj)


    def create_ident_dict(item_list: list[Type[classes.Hirarchy]]) -> dict[str, Type[classes.Hirarchy]]:
        return {item.identifier: item for item in item_list}

    def link_parents(xml_predefined_psets: list[etree._Element], xml_objects: list[etree._Element]) -> None:
        def fill_dict(xml_dict: dict[str, str], xml_obj: etree._Element) -> None:
            xml_dict[xml_obj.attrib.get(constants.IDENTIFIER)] = xml_obj.attrib.get(constants.PARENT)

        def iterate() -> None:
            for xml_predefined_pset in xml_predefined_psets:
                fill_dict(xml_property_set_dict, xml_predefined_pset)
                xml_attributes = xml_predefined_pset.find(constants.ATTRIBUTES)
                for xml_attribute in xml_attributes:
                    fill_dict(xml_attribute_dict, xml_attribute)

            for xml_object in xml_objects:
                fill_dict(xml_object_dict, xml_object)
                xml_property_sets = xml_object.find(constants.PROPERTY_SETS)
                for xml_property_set in xml_property_sets:
                    fill_dict(xml_property_set_dict, xml_property_set)
                    xml_attributes = xml_property_set.find(constants.ATTRIBUTES)
                    for xml_attribute in xml_attributes:
                        uuid = xml_attribute.attrib["identifer"]
                        if xml_attribute_dict.get(uuid) is not None:
                            print(f"ERROR DUPLICATED UUID {uuid}")
                        fill_dict(xml_attribute_dict, xml_attribute)

        def create_link(item_dict: dict[str, Type[classes.Hirarchy]], xml_dict: dict[str, str]):
            for ident, item in item_dict.items():
                parent_ident = xml_dict[str(ident)]
                parent_item = item_dict.get(parent_ident)
                if parent_item is not None:
                    parent_item.add_child(child=item)

        xml_property_set_dict = dict()
        xml_object_dict = dict()
        xml_attribute_dict = dict()
        iterate()

        obj_dict = create_ident_dict(classes.Object)
        property_set_dict = create_ident_dict(classes.PropertySet)
        attribute_dict = create_ident_dict(classes.Attribute)

        create_link(obj_dict, xml_object_dict)
        create_link(property_set_dict, xml_property_set_dict)
        create_link(attribute_dict, xml_attribute_dict)

    def link_aggregation() -> None:
        def create_node_dict() -> dict[str, [classes.Aggregation, object]]:

            id_node_dict = dict()
            for xml_node in xml_group_nodes:
                identifier = xml_node.attrib.get(constants.IDENTIFIER)
                obj = ident_dict[xml_node.attrib.get(constants.OBJECT.lower())]
                aggregation = classes.Aggregation(obj, identifier)
                id_node_dict[identifier] = (aggregation, xml_node)
            return id_node_dict

        id_node_dict = create_node_dict()

        for identifier, (aggregation, xml_node) in id_node_dict.items():
            parent_id = xml_node.attrib.get(constants.PARENT)
            is_root = xml_node.attrib.get(constants.IS_ROOT)
            connection_type = xml_node.attrib.get(constants.CONNECTION)
            if parent_id != constants.NONE:
                parent_node: classes.Aggregation = id_node_dict[parent_id][0]
                parent_node.add_child(aggregation, int(connection_type))

    xml_group_predef_psets = projekt_xml.find(constants.PREDEFINED_PSETS)
    xml_group_objects = projekt_xml.find(constants.OBJECTS)
    xml_group_nodes = projekt_xml.find(constants.NODES)

    import_property_sets(xml_group_predef_psets)
    ident_dict: dict[str, classes.Object] = dict()
    import_objects(xml_group_objects)

    link_parents(xml_group_predef_psets, xml_group_objects)
    link_aggregation()
