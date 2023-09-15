from __future__ import annotations

import json
import logging
import os

import jinja2

from . import classes
from .Template import MAPPING_TEMPLATE, HOME_DIR
from .constants import json_constants


def string_to_bool(text: str) -> bool | None:
    if text == str(True):
        return True
    elif text == str(False):
        return False
    else:
        return None


def create_mapping_script(project: classes.Project, pset_name: str, path: str):
    attrib_dict = dict()
    obj: classes.Object
    for obj in project.objects:
        klass = obj.ident_attrib.value[0]
        obj_dict = dict()
        for pset in obj.property_sets:
            pset_dict = dict()
            for attribute in pset.attributes:
                name = attribute.name
                data_format = attribute.data_type
                pset_dict[name] = data_format
            obj_dict[pset.name] = pset_dict
        attrib_dict[klass] = obj_dict
    file_loader = jinja2.FileSystemLoader(HOME_DIR)
    env = jinja2.Environment(loader=file_loader)
    env.trim_blocks = True
    env.lstrip_blocks = True

    template = env.get_template(MAPPING_TEMPLATE)
    code = template.render(attribute_dict=attrib_dict, pset_name=pset_name)
    with open(path, "w") as file:
        file.write(code)
    pass


def export_json(project: classes.Project, path: str) -> dict:
    def create_project_data(project_dict: dict) -> None:
        project_dict[json_constants.NAME] = project.name
        project_dict[json_constants.AUTHOR] = project.author
        project_dict[json_constants.VERSION] = project.version
        project_dict[json_constants.AGGREGATION_ATTRIBUTE] = project.aggregation_attribute
        project_dict[json_constants.AGGREGATION_PSET] = project.aggregation_pset
        project_dict[json_constants.CURRENT_PR0JECT_PHASE] = project.current_project_phase
        project_dict[json_constants.PROJECT_PHASES] = project.get_project_phase_list()

    def fill_basics(entity_dict, entity):
        """function gets called from all Entities"""
        entity_dict[json_constants.NAME] = entity.name
        entity_dict[json_constants.OPTIONAL] = entity.optional
        entity_dict[json_constants.PROJECT_PHASES] = entity.get_project_phase_dict()
        parent = None if entity.parent is None else entity.parent.uuid
        entity_dict[json_constants.PARENT] = parent
        entity_dict[json_constants.DESCRIPTION] = entity.description

    def create_attribute_entry(attributes_dict, attribute):
        attribute_dict = dict()
        fill_basics(attribute_dict, attribute)
        attribute_dict[json_constants.DATA_TYPE] = attribute.data_type
        attribute_dict[json_constants.VALUE_TYPE] = attribute.value_type
        attribute_dict[json_constants.CHILD_INHERITS_VALUE] = attribute.child_inherits_values
        attribute_dict[json_constants.REVIT_MAPPING] = attribute.revit_name
        attribute_dict[json_constants.VALUE] = attribute.value
        attributes_dict[attribute.uuid] = attribute_dict

    def create_pset_entry(psets_dict: dict, pset: classes.PropertySet):
        pset_dict = dict()
        fill_basics(pset_dict, pset)
        attributes_dict = dict()
        for attribute in pset.get_all_attributes():
            create_attribute_entry(attributes_dict, attribute)
        pset_dict[json_constants.ATTRIBUTES] = attributes_dict
        psets_dict[pset.uuid] = pset_dict

    def create_object_entry(objects_dict: dict, object: classes.Object):

        object_dict = dict()
        fill_basics(object_dict, object)

        if isinstance(obj.ifc_mapping, set):
            object_dict[json_constants.IFC_MAPPINGS] = list(object.ifc_mapping)
        else:
            object_dict[json_constants.IFC_MAPPINGS] = object.ifc_mapping

        psets_dict = dict()
        for pset in object.get_all_property_sets():
            create_pset_entry(psets_dict, pset)

        object_dict[json_constants.PROPERTY_SETS] = psets_dict
        object_dict[json_constants.ABBREVIATION] = object.abbreviation

        objects_dict[obj.uuid] = object_dict
        if isinstance(object.ident_attrib, classes.Attribute):
            object_dict[json_constants.IDENT_ATTRIBUTE] = object.ident_attrib.uuid
        else:
            object_dict[json_constants.IDENT_ATTRIBUTE] = object.ident_attrib

    def create_aggregation_entry(aggregations_dict, aggregation: classes.Aggregation):
        aggregation_dict = dict()
        fill_basics(aggregation_dict, aggregation)
        aggregation_dict[json_constants.OBJECT] = aggregation.object.uuid
        if aggregation.parent is not None:
            aggregation_dict[json_constants.PARENT] = aggregation.parent.uuid
        else:
            aggregation_dict[json_constants.PARENT] = aggregation.parent
        aggregation_dict[json_constants.CONNECTION] = aggregation.parent_connection
        aggregations_dict[aggregation.uuid] = aggregation_dict

    main_dict = dict()
    main_dict[json_constants.PROJECT] = dict()
    create_project_data(main_dict[json_constants.PROJECT])

    predef_pset_dict = dict()
    predefined_psets = project.get_predefined_psets()
    for entity in sorted(predefined_psets, key=lambda x: x.uuid):
        create_pset_entry(predef_pset_dict, entity)
    main_dict[json_constants.PREDEFINED_PSETS] = predef_pset_dict

    objects_dict = dict()
    for obj in project.get_all_objects():
        create_object_entry(objects_dict, obj)

    main_dict[json_constants.OBJECTS] = objects_dict

    aggregations_dict = dict()
    for aggregation in project.get_all_aggregations():
        create_aggregation_entry(aggregations_dict, aggregation)
    main_dict[json_constants.AGGREGATIONS] = aggregations_dict
    with open(path, "w") as file:
        json.dump(main_dict, file, indent=2)

    return main_dict


def import_json(project: classes.Project, path: str):
    if not os.path.isfile(path):
        return
    parent_dict = {}
    aggregation_parent_dict: dict[classes.Aggregation, (str, int)] = dict()

    with open(path, "r") as file:
        main_dict: dict = json.load(file)

    def load_project_data(project_dict: dict):
        project.name = project_dict.get(json_constants.NAME)
        project.author = project_dict.get(json_constants.AUTHOR)
        project.version = project_dict.get(json_constants.VERSION)

        pset = project_dict.get(json_constants.AGGREGATION_PSET)
        attribute = project_dict.get(json_constants.AGGREGATION_ATTRIBUTE)
        current_project_phase = project_dict.get(json_constants.CURRENT_PR0JECT_PHASE)
        project_phases = project_dict.get(json_constants.PROJECT_PHASES)

        if pset is not None:
            project.aggregation_pset = pset
        if attribute is not None:
            project.aggregation_attribute = attribute
        if project_phases is not None and isinstance(project_phases, list):
            project._project_phases = project_phases

        if current_project_phase is not None:
            project.current_project_phase = current_project_phase
        elif project.get_project_phase_list():
            project.current_project_phase = project.get_project_phase_list()[0]

    def load_basics(element_dict: dict) -> (str, str, str):
        name = element_dict[json_constants.NAME]
        description = element_dict[json_constants.DESCRIPTION]
        optional = element_dict[json_constants.OPTIONAL]
        parent = element_dict[json_constants.PARENT]
        project_phases = element_dict.get(json_constants.PROJECT_PHASES)
        if not isinstance(project_phases, dict):
            project_phases = None
        return name, description, optional, parent, project_phases

    def load_object(object_dict, identifier):
        name, description, optional, parent, project_phases = load_basics(object_dict)
        ifc_mapping = object_dict[json_constants.IFC_MAPPINGS]
        if isinstance(ifc_mapping, list):
            ifc_mapping = set(ifc_mapping)

        abbreviation = object_dict.get(json_constants.ABBREVIATION)

        obj = classes.Object(name=name, ident_attrib=None, uuid=identifier, ifc_mapping=ifc_mapping,
                             description=description, optional=optional, abbreviation=abbreviation, project=project,
                             project_phases=project_phases)
        property_sets_dict = object_dict[json_constants.PROPERTY_SETS]
        for ident, pset_dict in property_sets_dict.items():
            load_pset(pset_dict, ident, obj)
        ident_attrib_id = object_dict[json_constants.IDENT_ATTRIBUTE]
        ident_attrib = classes.get_element_by_uuid(ident_attrib_id)
        obj.ident_attrib = ident_attrib
        parent_dict[obj] = parent

    def load_pset(pset_dict: dict, identifier: str, obj: classes.Object | None) -> None:
        name, description, optional, parent, project_phases = load_basics(pset_dict)
        pset = classes.PropertySet(name=name, obj=obj, uuid=identifier, description=description, optional=optional,
                                   project=project, project_phases=project_phases)
        attributes_dict = pset_dict[json_constants.ATTRIBUTES]
        for ident, attribute_dict in attributes_dict.items():
            load_attribute(attribute_dict, ident, pset)
        parent_dict[pset] = parent

    def load_attribute(attribute_dict: dict, identifier: str, property_set: classes.PropertySet) -> None:
        name, description, optional, parent, project_phases = load_basics(attribute_dict)
        value = attribute_dict[json_constants.VALUE]
        value_type = attribute_dict[json_constants.VALUE_TYPE]
        data_type = attribute_dict[json_constants.DATA_TYPE]
        child_inherits_value = attribute_dict[json_constants.CHILD_INHERITS_VALUE]
        revit_mapping = attribute_dict[json_constants.REVIT_MAPPING]
        attribute = classes.Attribute(property_set=property_set, name=name, value=value, value_type=value_type,
                                      data_type=data_type,
                                      child_inherits_values=child_inherits_value, uuid=identifier,
                                      description=description, optional=optional, revit_mapping=revit_mapping,
                                      project=project, project_phases=project_phases)
        parent_dict[attribute] = parent

    def load_dict(dict_name: str) -> dict | None:
        return_dict = main_dict.get(dict_name)
        if return_dict is None:
            logging.error(f"loading Error: {dict_name} doesn't exist!")
            return {}
        return return_dict

    def load_parents():
        def find_parent(element):
            print(f"gesucht: {element.name}")
            for test_el,uuid in parent_dict.items():
                if type(test_el) != type(element):
                    continue
                if uuid not in uuid_dict:
                    continue
                if test_el == element:
                    continue
                if test_el.parent is not None:
                    continue

                if test_el.name != element.name:
                    continue

                if isinstance(test_el,classes.Attribute):
                    if test_el.value == element.value:
                        return uuid
                        continue
                return uuid


        uuid_dict = classes.get_uuid_dict()
        for element, uuid in parent_dict.items():
            if uuid is not None:
                if uuid not in uuid_dict:
                    uuid = find_parent(element)
                    print(f"neue uuid: {uuid}")
                if uuid is None:
                    continue
                uuid_dict[uuid].add_child(element)

    def load_aggregation(aggregation_dict: dict, identifier: str, ):
        name, description, optional, parent, project_phases = load_basics(aggregation_dict)
        object_uuid = aggregation_dict[json_constants.OBJECT]
        obj = classes.get_element_by_uuid(object_uuid)
        parent_connection = aggregation_dict[json_constants.CONNECTION]
        aggregation = classes.Aggregation(obj, parent_connection, identifier, description, optional, project_phases)
        aggregation_parent_dict[aggregation] = (parent, parent_connection)

    def build_aggregation_structure():
        for aggregation, (uuid, connection_type) in aggregation_parent_dict.items():
            parent = classes.get_element_by_uuid(uuid)
            if parent is not None:
                parent.add_child(aggregation, connection_type)

    def fill_missing_project_phases():
        phases = project.get_project_phase_list()
        for item in project.get_all_hirarchy_items():
            phase_dict = item.get_project_phase_dict()
            for phase in phases:
                if phase not in phase_dict:
                    item.add_project_phase(phase, True)

    project_dict = main_dict.get(json_constants.PROJECT)
    if project_dict is None:
        logging.warning(f"{json_constants.PROJECT}-dict doesn't exist unable to load Author, Name and Version")
    else:
        load_project_data(project_dict)

    predefined_psets_dict = load_dict(json_constants.PREDEFINED_PSETS)

    for ident, pset_dict in predefined_psets_dict.items():
        load_pset(pset_dict, ident, None)

    objects_dict = load_dict(json_constants.OBJECTS)
    for ident, object_dict in objects_dict.items():
        load_object(object_dict, ident)

    aggregations_dict = load_dict(json_constants.AGGREGATIONS)
    for ident, aggreg_dict in aggregations_dict.items():
        load_aggregation(aggreg_dict, ident)

    load_parents()
    build_aggregation_structure()
    fill_missing_project_phases()
    return main_dict
