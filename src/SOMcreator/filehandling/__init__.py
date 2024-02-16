from __future__ import annotations

import os
import json
import SOMcreator
from .typing import MainDict
from typing import Type,TYPE_CHECKING
from . import constants, core, project, property_set, obj, aggregation

if TYPE_CHECKING:
    from SOMcreator.classes import Project

parent_dict = dict()
aggregation_dict = dict()
phase_list = list()
use_case_list = list()


def open_json(cls: Type[Project], path: str):
    SOMcreator.filehandling.parent_dict = dict()

    if not os.path.isfile(path):
        return

    with open(path, "r") as file:
        main_dict: MainDict = json.load(file)

    project_dict = main_dict.get(constants.PROJECT)
    SOMcreator.filehandling.phase_list, SOMcreator.filehandling.use_case_list = core.get_filter_lists(project_dict)

    proj, project_dict = project.load_project(cls, main_dict)
    property_set.load_predefined(proj, main_dict)

    obj.load(proj, main_dict)

    aggregation.load(proj, main_dict)

    aggregation.load_parents()
    aggregation.build_aggregation_structure()
    return proj, main_dict
