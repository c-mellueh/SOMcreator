import SOMcreator
from SOMcreator.classes import Project, UseCase, Phase, Hirarchy


def _calculate_new_filter_matrix(new_project: Project, item: Hirarchy, phase_mapping, use_case_mapping):
    new_filter_matrix = list()
    for new_phase in new_project.get_project_phase_list():
        old_phase = phase_mapping.get(new_phase)
        filter_list = list()
        for new_use_case in new_project.get_use_case_list():
            old_use_case = use_case_mapping.get(new_use_case)
            if old_phase and old_use_case:
                filter_list.append(item.get_filter_state(old_phase, old_use_case))
            else:
                filter_list.append(True)
        new_filter_matrix.append(filter_list)
    return new_filter_matrix


def _merge_dicts(d1: dict, d2: dict):
    for key, value2 in d2.items():
        value1 = d1.get(key)
        if isinstance(value1, dict) and isinstance(value2, dict):
            _merge_dicts(value1, value2)
        elif value1 is None:
            d1[key] = value2
    return d1


def _add_item(project, item, phase_mapping, use_case_mapping):
    new_filter_matrix = _calculate_new_filter_matrix(project, item, phase_mapping, use_case_mapping)
    project.add_item(item)
    item._project = project
    item._filter_matrix = new_filter_matrix


def _import_object(proj, obj, old_predefined_psets_mapping, phase_mapping, use_case_mapping):
    _add_item(proj, obj, phase_mapping, use_case_mapping)
    for property_set in obj.get_all_property_sets():
        _import_pset(proj, property_set, old_predefined_psets_mapping, phase_mapping, use_case_mapping)

    for aggregation in obj.aggregations:
        _add_item(proj, aggregation, phase_mapping, use_case_mapping)


def _import_pset(proj, property_set, old_predefined_psets_mapping, phase_mapping, use_case_mapping):
    parent = old_predefined_psets_mapping.get(property_set.parent)
    _add_item(proj, property_set, phase_mapping, use_case_mapping)

    if parent is not None:
        property_set.parent = parent
        for attribute in property_set.get_all_attributes():
            _import_attribute(proj, attribute, phase_mapping, use_case_mapping, parent)
    else:
        for attribute in property_set.get_all_attributes():
            _import_attribute(proj, attribute, phase_mapping, use_case_mapping)


def _import_attribute(proj, attribute, phase_mapping, use_case_mapping, parent_pset: SOMcreator.PropertySet = None):
    if parent_pset:
        parent_attribute = {a.name: a for a in parent_pset.attributes}.get(attribute.name)
        if parent_attribute:
            attribute.parent = parent_attribute
    _add_item(proj, attribute, phase_mapping, use_case_mapping)


def merge_projects(project_1: Project, project_2: Project, phase_mapping: dict[Phase, Phase],
                   use_case_mapping: dict[UseCase, UseCase]):
    identifier_list = {o.ident_value for o in project_1.get_all_objects()}
    old_predefined_psets_mapping = {p: p for p in project_2.get_predefined_psets()}
    predefined_pset_dict = {p.name: p for p in project_1.get_predefined_psets()}

    for predefined_pset in old_predefined_psets_mapping.keys():
        new_pset = predefined_pset_dict.get(predefined_pset.name)
        if not new_pset:
            _add_item(project_1, predefined_pset, phase_mapping, use_case_mapping)
        else:
            old_predefined_psets_mapping[predefined_pset] = new_pset

    for obj in project_2.get_all_objects():
        if obj.ident_value not in identifier_list:
            _import_object(project_1, obj, old_predefined_psets_mapping, phase_mapping, use_case_mapping)

    project_1.plugin_dict = _merge_dicts(project_1.plugin_dict, project_2.plugin_dict)
    project_1.import_dict = _merge_dicts(project_1.import_dict, project_2.import_dict)
