from __future__ import annotations

from typing import TypedDict
import json
import logging
import os
import jinja2

from . import classes
from .Template import MAPPING_TEMPLATE, HOME_DIR
from .constants.value_constants import OLD_DATATYPE_DICT


class StandardDict(TypedDict):
    name: str
    optional: bool
    filter_matrix: list[list[bool]]
    parent: str | None
    description: str


class MainDict(TypedDict):
    Project: ProjectDict
    PredefinedPropertySets: dict[str, PropertySetDict]
    Objects: dict[str, ObjectDict]
    Aggregations: dict[str, AggregationDict]
    AggregationScenes: dict[str, AggregationScene]


class ProjectDict(TypedDict):
    name: str
    author: str
    version: str
    AggregationAttributeName: str
    AggregationPsetName: str
    current_project_phase: int
    current_use_case: int
    ProjectPhases: list[FilterDict]
    UseCases: list[FilterDict]


class ObjectDict(StandardDict):
    IfcMappings: list[str]
    abbreviation: str
    ident_attribute: str
    PropertySets: dict[str, PropertySetDict]


class PropertySetDict(StandardDict):
    Attributes: dict[str, AttributeDict]


class AttributeDict(StandardDict):
    data_type: str
    value_type: str
    child_inherits_value: bool
    revit_mapping: str
    Value: list[str] | list[float] | list[[float, float]]


class AggregationDict(StandardDict):
    Object: str | None
    connection: int
    x_pos: float
    y_pos: float


class AggregationScene(TypedDict):
    Nodes: list[str]


class FilterDict(TypedDict):
    name: str
    long_name: str
    description: str


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
    def create_filter_dict(filter_list: list[classes.Phase] | list[classes.UseCase]) -> list[FilterDict]:
        fl = list()
        for fil in filter_list:
            fl.append({
                "name":        fil.name,
                "long_name":   fil.long_name,
                "description": fil.description
            })
        return fl

    def create_project_data(project_dict: ProjectDict) -> None:
        project_dict[NAME] = project.name
        project_dict[AUTHOR] = project.author
        project_dict[VERSION] = project.version
        project_dict[AGGREGATION_ATTRIBUTE] = project.aggregation_attribute
        project_dict[AGGREGATION_PSET] = project.aggregation_pset
        project_dict[CURRENT_PR0JECT_PHASE] = project.get_project_phase_list().index(project.current_project_phase)
        project_dict[CURRENT_USE_CASE] = project.get_use_case_list().index(project.current_use_case)
        project_dict[PROJECT_PHASES] = create_filter_dict(project.get_project_phase_list())
        project_dict[USE_CASES] = create_filter_dict(project.get_use_case_list())

    def create_filter_matrix(element: classes.ClassTypes):
        proj = element.project
        phases = proj.get_project_phase_list()
        use_cases = proj.get_use_case_list()
        matrix = list()
        for phase in phases:
            phase_list = list()
            for use_case in use_cases:
                phase_list.append(element.get_filter_state(phase, use_case))
            matrix.append(phase_list)
        return matrix

    def fill_basics(entity_dict: ObjectDict | PropertySetDict | AttributeDict | AggregationDict,
                    element: classes.ClassTypes) -> None:
        """function gets called from all Entities"""
        entity_dict[NAME] = element.name
        entity_dict[OPTIONAL] = element.optional
        entity_dict[FILTER_MATRIX] = create_filter_matrix(element)
        parent = None if element.parent is None else element.parent.uuid
        entity_dict[PARENT] = parent
        entity_dict[DESCRIPTION] = element.description

    def create_attribute_entry(attribute: classes.Attribute) -> AttributeDict:
        attribute_dict: AttributeDict = dict()
        fill_basics(attribute_dict, attribute)
        attribute_dict[DATA_TYPE] = attribute.data_type
        attribute_dict[VALUE_TYPE] = attribute.value_type
        attribute_dict[CHILD_INHERITS_VALUE] = attribute.child_inherits_values
        attribute_dict[REVIT_MAPPING] = attribute.revit_name
        attribute_dict[VALUE] = attribute.value
        return attribute_dict

    def create_pset_entry(pset: classes.PropertySet) -> PropertySetDict:
        pset_dict: PropertySetDict = dict()
        fill_basics(pset_dict, pset)
        attributes_dict = dict()
        for attribute in pset.get_all_attributes():
            new_dict = create_attribute_entry(attribute)
            attributes_dict[attribute.uuid] = new_dict
        pset_dict[ATTRIBUTES] = attributes_dict
        return pset_dict

    def create_object_entry(element: classes.Object) -> ObjectDict:

        object_dict: ObjectDict = dict()
        fill_basics(object_dict, element)

        if isinstance(element.ifc_mapping, set):
            object_dict[IFC_MAPPINGS] = list(element.ifc_mapping)
        else:
            object_dict[IFC_MAPPINGS] = list(element.ifc_mapping)

        psets_dict = dict()
        for pset in element.get_all_property_sets():
            psets_dict[pset.uuid] = create_pset_entry(pset)

        object_dict[PROPERTY_SETS] = psets_dict
        object_dict[ABBREVIATION] = element.abbreviation

        if isinstance(element.ident_attrib, classes.Attribute):
            object_dict[IDENT_ATTRIBUTE] = element.ident_attrib.uuid
        else:
            object_dict[IDENT_ATTRIBUTE] = element.ident_attrib

        return object_dict

    def create_aggregation_entry(element: classes.Aggregation) -> AggregationDict:
        aggregation_dict: AggregationDict = dict()
        fill_basics(aggregation_dict, element)
        aggregation_dict[OBJECT] = element.object.uuid
        if element.parent is not None:
            aggregation_dict[PARENT] = element.parent.uuid
        else:
            aggregation_dict[PARENT] = str(element.parent)
        aggregation_dict[CONNECTION] = element.parent_connection
        return aggregation_dict

    main_dict: MainDict = dict()
    main_dict[PROJECT] = dict()
    create_project_data(main_dict[PROJECT])

    main_dict[PREDEFINED_PSETS] = dict()
    for predefined_property_set in sorted(project.get_predefined_psets(), key=lambda x: x.uuid):
        main_dict[PREDEFINED_PSETS][predefined_property_set.uuid] = create_pset_entry(predefined_property_set)

    main_dict[OBJECTS] = dict()
    for obj in sorted(project.get_all_objects(), key=lambda o: o.uuid):
        main_dict[OBJECTS][obj.uuid] = create_object_entry(obj)

    main_dict[AGGREGATIONS] = dict()
    for aggregation in project.get_all_aggregations():
        main_dict[AGGREGATIONS][aggregation.uuid] = create_aggregation_entry(aggregation)

    with open(path, "w") as file:
        json.dump(main_dict, file)

    return main_dict


def _get_filter_lists(project_dict: ProjectDict):
    project_phases = project_dict.get(PROJECT_PHASES)
    use_cases = project_dict.get(USE_CASES)
    phase_list = list()
    use_case_list = list()
    if project_phases is not None and isinstance(project_phases, list):
        for phase in project_phases:
            if isinstance(phase, str):
                phase_list.append(classes.Phase(phase, phase, ""))
            else:
                phase_list.append(classes.Phase(phase["name"], phase.get("long_name"), phase.get("description")))

    if use_cases is not None and isinstance(use_cases, list):
        for use_case in use_cases:
            if isinstance(use_case, str):
                use_case_list.append(classes.Phase(use_case, use_case, ""))
            else:
                use_case_list.append(
                    classes.UseCase(use_case["name"], use_case.get("long_name"), use_case.get("description")))
    return phase_list, use_case_list


def import_json(project: classes.Project, path: str):
    def load_project_data() -> None:
        project.name = project_dict.get(NAME)
        project.author = project_dict.get(AUTHOR)
        project.version = project_dict.get(VERSION)

        aggregation_pset_name = project_dict.get(AGGREGATION_PSET)
        aggregation_attribute = project_dict.get(AGGREGATION_ATTRIBUTE)
        current_project_phase = project_dict.get(CURRENT_PR0JECT_PHASE)
        current_use_case = project_dict.get(CURRENT_USE_CASE)
        if aggregation_pset_name is not None:
            project.aggregation_pset = aggregation_pset_name
        if aggregation_attribute is not None:
            project.aggregation_attribute = aggregation_attribute
        phase_list, use_case_list = _get_filter_lists(project_dict)
        for phase in phase_list:
            project.add_project_phase(phase)
        for use_case in use_case_list:
            project.add_use_case(use_case)
        if current_project_phase is not None:
            if isinstance(current_project_phase, str):
                project.current_project_phase = project.get_project_phase_by_name(current_project_phase)
            else:
                project.current_project_phase = project.get_project_phase_list()[current_project_phase]
        elif project.get_project_phase_list():
            project.current_project_phase = project.get_project_phase_list()[0]

        if current_use_case is not None:
            if isinstance(current_use_case, str):
                project.current_use_case = project.get_use_case_by_name(current_use_case)
            else:
                project.current_use_case = project.get_use_case_list()[current_use_case]
        elif project.get_use_case_list():
            project.current_use_case = project.get_use_case_list()[0]

    def load_basics(element_dict: StandardDict) -> tuple[str, str, bool, str, list[list[bool]]]:
        def get_value(d: dict, p: str) -> bool:
            return d.get(p) if d.get(p) is not None else True

        name = element_dict[NAME]
        description = element_dict[DESCRIPTION]
        optional = element_dict[OPTIONAL]
        parent = element_dict[PARENT]
        matrix = element_dict.get(FILTER_MATRIX)
        phase_list, use_case_list = _get_filter_lists(project_dict)
        matrix_list = list()
        for _ in project.get_project_phase_list():
            matrix_list.append([True for __ in project.get_use_case_list()])

        if matrix is None:  # handle deprecated file types
            matrix = list()
            file_phases: list[bool] = element_dict.get(PROJECT_PHASES)
            if isinstance(file_phases, dict):  # deprecated
                output_phases = [get_value(file_phases, phase.name) for phase in project.get_project_phase_list()]
            elif file_phases is None:
                output_phases = [True for _ in project.get_project_phase_list()]
            else:
                output_phases = [True for _ in project.get_project_phase_list()]
                for output_index, existing_phase in enumerate(project.get_project_phase_list()):
                    if existing_phase in phase_list:
                        value = file_phases[phase_list.index(existing_phase)]
                        output_phases[output_index] = value

            file_use_cases: list[bool] = element_dict.get(USE_CASES)
            if file_use_cases is None:
                output_use_cases = [True for _ in project.get_use_case_list()]
            else:
                output_use_cases = [True for _ in project.get_use_case_list()]
                for output_index, existing_use_case in enumerate(project.get_use_case_list()):
                    if existing_use_case in use_case_list:
                        value = file_use_cases[use_case_list.index(existing_use_case)]
                        output_use_cases[output_index] = value

            for phase_index, phase in enumerate(output_phases):
                pl = list()
                for use_case_index, use_case in enumerate(output_use_cases):
                    pl.append(bool(output_phases[phase_index] and output_use_cases[use_case_index]))
                matrix.append(pl)
        return name, description, optional, parent, matrix

    def load_object(object_dict: ObjectDict, identifier: str) -> None:
        name, description, optional, parent, filter_matrix = load_basics(object_dict)
        ifc_mapping = object_dict[IFC_MAPPINGS]
        if isinstance(ifc_mapping, list):
            ifc_mapping = set(ifc_mapping)

        abbreviation = object_dict.get(ABBREVIATION)

        obj = classes.Object(name=name, ident_attrib=None, uuid=identifier, ifc_mapping=ifc_mapping,
                             description=description, optional=optional, abbreviation=abbreviation, project=project,
                             filter_matrix=filter_matrix)
        property_sets_dict = object_dict[PROPERTY_SETS]
        for ident, pset_dict in property_sets_dict.items():
            load_pset(pset_dict, ident, obj)
        ident_attrib_id = object_dict[IDENT_ATTRIBUTE]
        ident_attrib = classes.get_element_by_uuid(ident_attrib_id)
        obj.ident_attrib = ident_attrib
        parent_dict[obj] = parent

    def load_pset(pset_dict: PropertySetDict, identifier: str, obj: classes.Object | None) -> None:
        name, description, optional, parent, filter_matrix = load_basics(pset_dict)
        pset = classes.PropertySet(name=name, obj=obj, uuid=identifier, description=description, optional=optional,
                                   project=project, filter_matrix=filter_matrix)
        attributes_dict = pset_dict[ATTRIBUTES]
        for ident, attribute_dict in attributes_dict.items():
            load_attribute(attribute_dict, ident, pset)
        parent_dict[pset] = parent

    def load_attribute(attribute_dict: dict, identifier: str, property_set: classes.PropertySet, ) -> None:
        name, description, optional, parent, filter_matrix = load_basics(attribute_dict)
        value = attribute_dict[VALUE]
        value_type = attribute_dict[VALUE_TYPE]
        data_type = attribute_dict[DATA_TYPE]

        # compatibility for Datatype import that uses XML-Datatypes such as xs:string
        if data_type in OLD_DATATYPE_DICT:
            data_type = OLD_DATATYPE_DICT[data_type]

        child_inherits_value = attribute_dict[CHILD_INHERITS_VALUE]
        revit_mapping = attribute_dict[REVIT_MAPPING]
        attribute = classes.Attribute(property_set=property_set, name=name, value=value, value_type=value_type,
                                      data_type=data_type,
                                      child_inherits_values=child_inherits_value, uuid=identifier,
                                      description=description, optional=optional, revit_mapping=revit_mapping,
                                      project=project, filter_matrix=filter_matrix)
        parent_dict[attribute] = parent

    def load_parents():
        def find_parent(element: classes.ClassTypes):
            for test_el, identifier in parent_dict.items():
                if type(test_el) is not type(element):
                    continue
                if identifier not in uuid_dict:
                    continue
                if test_el == element:
                    continue
                if test_el.parent is not None:
                    continue

                if test_el.name != element.name:
                    continue

                if isinstance(test_el, classes.Attribute):
                    if test_el.value == element.value:
                        return identifier
                return identifier

        uuid_dict = classes.get_uuid_dict()
        for entity, uuid in parent_dict.items():
            if uuid is None:
                continue
            if uuid not in uuid_dict:
                uuid = find_parent(entity)
            if uuid is None:
                continue
            uuid_dict[uuid].add_child(entity)

    def load_aggregation(aggregation_dict: dict, identifier: str, ):
        name, description, optional, parent, filter_matrix = load_basics(aggregation_dict)
        object_uuid = aggregation_dict[OBJECT]
        obj = classes.get_element_by_uuid(object_uuid)
        parent_connection = aggregation_dict[CONNECTION]
        aggregation = classes.Aggregation(obj=obj, parent_connection=parent_connection, uuid=identifier,
                                          description=description, optional=optional, filter_matrix=filter_matrix)
        aggregation_parent_dict[aggregation] = (parent, parent_connection)

    def build_aggregation_structure():
        for aggregation, (uuid, connection_type) in aggregation_parent_dict.items():
            parent = classes.get_element_by_uuid(uuid)
            if parent is None:
                continue
            parent.add_child(aggregation, connection_type)

    def check_dict(d: dict | None, d_name: str) -> bool:
        if d is None:
            logging.error(f"loading Error: {d_name} doesn't exist!")
            return True
        return False

    if not os.path.isfile(path):
        return
    parent_dict: dict[classes.ClassTypes, str] = {}
    aggregation_parent_dict: dict[classes.Aggregation, tuple[str, int]] = dict()

    with open(path, "r") as file:
        main_dict: MainDict = json.load(file)

    project_dict = main_dict.get(PROJECT)
    load_project_data()

    predef_pset_dict = main_dict.get(PREDEFINED_PSETS)
    predef_pset_dict = dict() if check_dict(predef_pset_dict, PREDEFINED_PSETS) else predef_pset_dict

    for uuid_ident, entity_dict in predef_pset_dict.items():
        load_pset(entity_dict, uuid_ident, None)

    objects_dict: dict[str, ObjectDict] = main_dict.get(OBJECTS)
    objects_dict = dict() if check_dict(objects_dict, OBJECTS) else objects_dict

    for uuid_ident, entity_dict in objects_dict.items():
        load_object(entity_dict, uuid_ident)

    aggregations_dict: dict[str, AggregationDict] = main_dict.get(AGGREGATIONS)
    aggregations_dict = dict() if check_dict(aggregations_dict, AGGREGATIONS) else aggregations_dict
    for uuid_ident, entity_dict in aggregations_dict.items():
        load_aggregation(entity_dict, uuid_ident)

    load_parents()
    build_aggregation_structure()
    return main_dict


DESCRIPTION = "description"
OPTIONAL = "optional"
CURRENT_PR0JECT_PHASE = "current_project_phase"
CURRENT_USE_CASE = "current_use_case"
PROJECT_PHASES = "ProjectPhases"
USE_CASES = "UseCases"
FILTER_MATRIX = "filter_matrix"
AGGREGATION_PSET = "AggregationPsetName"
AGGREGATION_ATTRIBUTE = "AggregationAttributeName"
PREDEFINED_PSETS = "PredefinedPropertySets"
PROPERTY_SETS = "PropertySets"
IDENT_ATTRIBUTE = "ident_attribute"
ATTRIBUTES = "Attributes"
OBJECT = "Object"
OBJECTS = "Objects"
AGGREGATIONS = "Aggregations"
NAME = "name"
PARENT = "parent"
DATA_TYPE = "data_type"
VALUE_TYPE = "value_type"
CHILD_INHERITS_VALUE = "child_inherits_value"
PROJECT = "Project"
VERSION = "version"
AUTHOR = "author"
X_POS = "x_pos"
Y_POS = "y_pos"
CONNECTION = "connection"
IFC_MAPPINGS = "IfcMappings"
IFC_MAPPING = "IfcMapping"
ABBREVIATION = "abbreviation"
REVIT_MAPPING = "revit_mapping"
VALUE = "Value"
IGNORE_PSET = "IFC"
