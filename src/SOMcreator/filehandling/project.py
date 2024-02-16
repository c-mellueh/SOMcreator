from __future__ import annotations
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from SOMcreator import Project
from .constants import PROJECT, NAME, AUTHOR, VERSION, AGGREGATION_PSET, AGGREGATION_ATTRIBUTE, CURRENT_PR0JECT_PHASE, \
    CURRENT_USE_CASE, FILTER_MATRIX
from SOMcreator.filehandling import core


def load_project(cls: Type[Project], main_dict) -> tuple[Project, dict]:
    project_dict = main_dict.get(PROJECT)
    name = project_dict.get(NAME)
    author = project_dict.get(AUTHOR)
    version = project_dict.get(VERSION)

    aggregation_pset_name = project_dict.get(AGGREGATION_PSET)
    aggregation_attribute = project_dict.get(AGGREGATION_ATTRIBUTE)
    current_project_phase = project_dict.get(CURRENT_PR0JECT_PHASE)
    current_use_case = project_dict.get(CURRENT_USE_CASE)
    filter_matrix = project_dict.get(FILTER_MATRIX)

    phase_list, use_case_list = core.get_filter_lists(project_dict)

    if filter_matrix is None:
        filter_matrix = list()

    proj = cls(name, author, phase_list, use_case_list, filter_matrix)
    if aggregation_pset_name is not None:
        proj.aggregation_pset = aggregation_pset_name
    if aggregation_attribute is not None:
        proj.aggregation_attribute = aggregation_attribute

    if current_project_phase is not None:
        if isinstance(current_project_phase, str):
            proj.current_project_phase = proj.get_project_phase_by_name(current_project_phase)
        else:
            proj.current_project_phase = proj.get_project_phase_list()[current_project_phase]
    elif proj.get_project_phase_list():
        proj.current_project_phase = proj.get_project_phase_list()[0]

    if current_use_case is not None:
        if isinstance(current_use_case, str):
            proj.current_use_case = proj.get_use_case_by_name(current_use_case)
        else:
            proj.current_use_case = proj.get_use_case_list()[current_use_case]
    elif proj.get_use_case_list():
        proj.current_use_case = proj.get_use_case_list()[0]
    proj.version = version
    return proj, project_dict
