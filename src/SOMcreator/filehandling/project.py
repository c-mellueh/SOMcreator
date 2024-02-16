from __future__ import annotations
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from SOMcreator import Project
from .constants import PROJECT, NAME, AUTHOR, VERSION, AGGREGATION_PSET, AGGREGATION_ATTRIBUTE, CURRENT_PR0JECT_PHASE, \
    CURRENT_USE_CASE, FILTER_MATRIX, PROJECT_PHASES, USE_CASES
from .typing import ProjectDict, FilterDict, MainDict
from SOMcreator.filehandling import core
from SOMcreator import classes


def load(cls: Type[Project], main_dict) -> tuple[Project, dict]:
    project_dict = main_dict.get(PROJECT)
    core.remove_part_of_dict(PROJECT)

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


def write(project, main_dict: MainDict) -> None:
    main_dict[PROJECT] = dict()
    project_dict: ProjectDict = main_dict[PROJECT]
    project_dict[NAME] = project.name
    project_dict[AUTHOR] = project.author
    project_dict[VERSION] = project.version
    project_dict[AGGREGATION_ATTRIBUTE] = project.aggregation_attribute
    project_dict[AGGREGATION_PSET] = project.aggregation_pset
    project_dict[CURRENT_PR0JECT_PHASE] = project.get_project_phase_list().index(project.current_project_phase)
    project_dict[CURRENT_USE_CASE] = project.get_use_case_list().index(project.current_use_case)
    project_dict[PROJECT_PHASES] = _write_filter_dict(project.get_project_phase_list())
    project_dict[USE_CASES] = _write_filter_dict(project.get_use_case_list())
    project_dict[FILTER_MATRIX] = project.get_filter_matrix()


def _write_filter_dict(filter_list: list[classes.Phase] | list[classes.UseCase]) -> list[FilterDict]:
    fl = list()
    for fil in filter_list:
        fl.append({
            "name":        fil.name,
            "long_name":   fil.long_name,
            "description": fil.description
        })
    return fl
