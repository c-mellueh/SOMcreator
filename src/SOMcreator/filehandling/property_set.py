from __future__ import annotations
import SOMcreator
from SOMcreator import classes
from SOMcreator.filehandling import core
from SOMcreator.filehandling.constants import PREDEFINED_PSETS, ATTRIBUTES
from SOMcreator.filehandling import attribute
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from SOMcreator.filehandling.typing import PropertySetDict
    from SOMcreator import Project


def load_pset(proj: Project, pset_dict: PropertySetDict, identifier: str, obj: classes.Object | None) -> None:
    name, description, optional, parent, filter_matrix = core.load_basics(proj, pset_dict)
    pset = classes.PropertySet(name=name, obj=obj, uuid=identifier, description=description, optional=optional,
                               project=proj, filter_matrix=filter_matrix)
    attributes_dict = pset_dict[ATTRIBUTES]
    for ident, attribute_dict in attributes_dict.items():
        attribute.load_attribute(proj, attribute_dict, ident, pset)
    SOMcreator.filehandling.parent_dict[pset] = parent


def load_predefined(project: Project, main_dict: dict):
    predef_pset_dict = main_dict.get(PREDEFINED_PSETS)
    predef_pset_dict = dict() if core.check_dict(predef_pset_dict, PREDEFINED_PSETS) else predef_pset_dict

    for uuid_ident, entity_dict in predef_pset_dict.items():
        load_pset(project, entity_dict, uuid_ident, None)
