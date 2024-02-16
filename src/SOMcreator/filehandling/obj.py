from __future__ import annotations
from typing import TYPE_CHECKING
from SOMcreator.filehandling.constants import IFC_MAPPINGS, ABBREVIATION, PROPERTY_SETS, IDENT_ATTRIBUTE, OBJECTS
from SOMcreator.filehandling import property_set
import SOMcreator
from SOMcreator import classes
from SOMcreator.filehandling import core

if TYPE_CHECKING:
    from SOMcreator import Project
    from SOMcreator.filehandling.typing import ObjectDict


def load_object(proj, object_dict: ObjectDict, identifier: str) -> None:
    name, description, optional, parent, filter_matrix = core.load_basics(proj,object_dict)
    ifc_mapping = object_dict[IFC_MAPPINGS]
    if isinstance(ifc_mapping, list):
        ifc_mapping = set(ifc_mapping)

    abbreviation = object_dict.get(ABBREVIATION)

    obj = classes.Object(name=name, ident_attrib=None, uuid=identifier, ifc_mapping=ifc_mapping,
                         description=description, optional=optional, abbreviation=abbreviation, project=proj,
                         filter_matrix=filter_matrix)
    property_sets_dict = object_dict[PROPERTY_SETS]
    for ident, pset_dict in property_sets_dict.items():
        property_set.load_pset(proj,pset_dict, ident, obj)
    ident_attrib_id = object_dict[IDENT_ATTRIBUTE]
    ident_attrib = classes.get_element_by_uuid(ident_attrib_id)
    obj.ident_attrib = ident_attrib
    SOMcreator.filehandling.parent_dict[obj] = parent


def load(proj: Project, main_dict: dict):
    objects_dict: dict[str, ObjectDict] = main_dict.get(OBJECTS)
    objects_dict = dict() if core.check_dict(objects_dict, OBJECTS) else objects_dict

    for uuid_ident, entity_dict in objects_dict.items():
        load_object(proj, entity_dict, uuid_ident)
