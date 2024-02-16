from __future__ import annotations

import os
import json
import SOMcreator
from .typing import MainDict
from typing import Type, TYPE_CHECKING
from . import constants, core, project, predefined_pset, property_set, obj, aggregation, inheritance

if TYPE_CHECKING:
    from SOMcreator.classes import Project
parent_dict = dict()
aggregation_dict = dict()
phase_list = list()
use_case_list = list()
plugin_dict = dict()


def open_json(cls: Type[Project], path: str):
    SOMcreator.filehandling.parent_dict = dict()

    if not os.path.isfile(path):
        return

    with open(path, "r") as file:
        main_dict: MainDict = json.load(file)

    SOMcreator.filehandling.plugin_dict = main_dict

    project_dict = main_dict.get(constants.PROJECT)
    SOMcreator.filehandling.phase_list, SOMcreator.filehandling.use_case_list = core.get_filter_lists(project_dict)

    proj, project_dict = project.load(cls, main_dict)
    predefined_pset.load(proj, main_dict)

    obj.load(proj, main_dict)

    aggregation.load(proj, main_dict)

    inheritance.calculate()
    aggregation.calculate()
    proj.plugin_dict = SOMcreator.filehandling.plugin_dict
    proj.import_dict = main_dict
    return proj


def export_json(proj: Project, path: str) -> dict:
    main_dict: MainDict = dict()
    project.write(proj, main_dict)
    predefined_pset.write(proj, main_dict)
    obj.write(proj, main_dict)
    aggregation.write(proj, main_dict)

    main_dict.update(proj.plugin_dict)
    with open(path, "w") as file:
        json.dump(main_dict, file)
    return main_dict
