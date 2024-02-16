from __future__ import annotations
import SOMcreator
from SOMcreator import classes
from SOMcreator.filehandling import core
from SOMcreator.filehandling.constants import OBJECT, CONNECTION, AGGREGATIONS, PARENT
from SOMcreator.filehandling.typing import AggregationDict

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from SOMcreator import Project
    from SOMcreator.filehandling.typing import MainDict


### Import ###

def load_parents():
    def find_parent(element: classes.ClassTypes):
        for test_el, identifier in SOMcreator.filehandling.parent_dict.items():
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
    for entity, uuid in SOMcreator.filehandling.parent_dict.items():
        if uuid is None:
            continue
        if uuid not in uuid_dict:
            uuid = find_parent(entity)
        if uuid is None:
            continue
        uuid_dict[uuid].add_child(entity)


def load_aggregation(proj, aggregation_dict: dict, identifier: str, ):
    name, description, optional, parent, filter_matrix = core.load_basics(proj, aggregation_dict)
    object_uuid = aggregation_dict[OBJECT]
    obj = classes.get_element_by_uuid(object_uuid)
    parent_connection = aggregation_dict[CONNECTION]
    aggregation = classes.Aggregation(obj=obj, parent_connection=parent_connection, uuid=identifier,
                                      description=description, optional=optional, filter_matrix=filter_matrix)
    SOMcreator.filehandling.aggregation_dict[aggregation] = (parent, parent_connection)


def build_aggregation_structure():
    for aggregation, (uuid, connection_type) in SOMcreator.filehandling.aggregation_dict.items():
        parent = classes.get_element_by_uuid(uuid)
        if parent is None:
            continue
        parent.add_child(aggregation, connection_type)


def load(proj: classes.Project, main_dict: dict):
    aggregations_dict: dict[str, AggregationDict] = main_dict.get(AGGREGATIONS)
    aggregations_dict = dict() if core.check_dict(aggregations_dict, AGGREGATIONS) else aggregations_dict
    for uuid_ident, entity_dict in aggregations_dict.items():
        load_aggregation(proj, entity_dict, uuid_ident)


### Export ###
def create_aggregation_entry(element: classes.Aggregation) -> AggregationDict:
    aggregation_dict: AggregationDict = dict()
    core.fill_basics(aggregation_dict, element)
    aggregation_dict[OBJECT] = element.object.uuid
    if element.parent is not None:
        aggregation_dict[PARENT] = element.parent.uuid
    else:
        aggregation_dict[PARENT] = str(element.parent)
    aggregation_dict[CONNECTION] = element.parent_connection
    return aggregation_dict


def save(proj: Project, main_dict: MainDict):
    main_dict[AGGREGATIONS] = dict()
    core.remove_part_of_dict(AGGREGATIONS)
    for aggregation in proj.get_all_aggregations():
        main_dict[AGGREGATIONS][aggregation.uuid] = create_aggregation_entry(aggregation)
