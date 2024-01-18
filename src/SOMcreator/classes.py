from __future__ import annotations

import logging
import os
from typing import Iterator, Union
from uuid import uuid4

import copy as cp
from anytree import AnyNode

from . import filehandling
from .constants import value_constants, json_constants


# Add child to Parent leads to reverse


def get_uuid_dict() -> dict[str, Object | PropertySet | Attribute | Aggregation]:
    pset_dict = {pset.uuid: pset for pset in PropertySet}
    object_dict = {obj.uuid: obj for obj in Object}
    attribute_dict = {attribute.uuid: attribute for attribute in Attribute}
    aggregation_dict = {aggreg.uuid: aggreg for aggreg in Aggregation}
    full_dict = pset_dict | object_dict | attribute_dict | aggregation_dict
    if None in full_dict:
        full_dict.pop(None)
    return full_dict


def get_element_by_uuid(uuid: str) -> Attribute | PropertySet | Object | Aggregation | None:
    if uuid is None:
        return None
    return get_uuid_dict().get(uuid)


class IterRegistry(type):
    _registry = set()
    """ Helper for Iteration"""

    def __iter__(self) -> Iterator[PropertySet | Object | Attribute | Aggregation]:
        return iter(sorted(list(self._registry), key=lambda x: x.name))

    def __len__(self) -> int:
        return len(self._registry)


class Project(object):
    def __init__(self, name: str = "", author: str | None = None) -> None:
        self._name = ""
        self._author = author
        self._version = "1.0.0"
        self.name = name
        self.aggregation_attribute = ""
        self.aggregation_pset = ""
        self._current_project_phase = "Standard"
        self._current_use_case = "Standard"
        self._project_phases = [self._current_project_phase]
        self._use_cases = [self._current_use_case]
        self.change_log = list()

    def get_predefined_psets(self) -> set[PropertySet]:
        return {pset for pset in PropertySet if pset.is_predefined}

    def get_main_attribute(self) -> (str, str):
        ident_attributes = dict()
        ident_psets = dict()
        for obj in self.objects:
            if obj.ident_attrib is None:
                continue
            ident_pset = obj.ident_attrib.property_set.name
            ident_attribute = obj.ident_attrib.name
            if ident_pset not in ident_psets:
                ident_psets[ident_pset] = 0
            if ident_attribute not in ident_attributes:
                ident_attributes[ident_attribute] = 0
            ident_psets[ident_pset] += 1
            ident_attributes[ident_attribute] += 1

        ident_attribute = (sorted(ident_attributes.items(), key=lambda x: x[1]))
        ident_pset = (sorted(ident_psets.items(), key=lambda x: x[1]))
        if ident_attribute and ident_pset:
            return ident_pset[0][0], ident_attribute[0][0]
        else:
            return "", ""

    def get_object_by_identifier(self, identifier: str) -> Object | None:
        return {obj.ident_value: obj for obj in self.objects}.get(identifier)

    def get_all_hirarchy_items(self) -> set[Object, PropertySet, Attribute, Aggregation]:
        hirarchy_set = set()
        for obj in self.objects:
            hirarchy_set.add(obj)
            for aggregation in obj.aggregations:
                hirarchy_set.add(aggregation)
            for pset in obj.property_sets:
                hirarchy_set.add(pset)
                for attribute in pset.attributes:
                    hirarchy_set.add(attribute)
        return hirarchy_set

    def get_project_phase_list(self) -> list[str]:
        return list(self._project_phases)

    def get_use_case_list(self) -> list[str]:
        return list(self._use_cases)

    def add_project_phase(self, project_phase_name: str, state: bool = True) -> None:
        if project_phase_name not in self._project_phases:
            self._project_phases.append(project_phase_name)
            for item in self.get_all_hirarchy_items():
                item.add_project_phase(project_phase_name, state)

    def add_use_case(self, use_case_name: str, state: bool = True) -> None:
        if use_case_name not in self._use_cases:
            self._use_cases.append(use_case_name)
            for item in self.get_all_hirarchy_items():
                item.add_use_case(use_case_name, state)

    def rename_project_phase(self, old_name: str, new_name: str) -> None:
        if old_name not in self._project_phases:
            logging.warning(f"Projektphase {old_name} nicht vorhanden")
            return
        if old_name == self.current_project_phase:
            self._current_project_phase = new_name

        index = self._project_phases.index(old_name)
        self._project_phases[index] = new_name

        for item in self.get_all_hirarchy_items():
            if old_name not in item.get_project_phase_dict():
                logging.warning(f"Projektphase {old_name} nicht vorhanden")
                continue
            value = item.get_project_phase_state(old_name)
            item.add_project_phase(project_phase_name=new_name, state=value)
            item.remove_project_phase(old_name)

    def rename_use_case(self, old_name: str, new_name: str) -> None:
        if old_name not in self._use_cases:
            logging.warning(f"UseCase {old_name} nicht vorhanden")
            return
        if old_name == self.current_use_case:
            self._current_use_case = new_name

        index = self._use_cases.index(old_name)
        self._use_cases[index] = new_name

        for item in self.get_all_hirarchy_items():
            if old_name not in item.get_use_case_dict():
                logging.warning(f"Use-case {old_name} nicht vorhanden")
                continue
            value = item.get_use_case_state(old_name)
            item.add_use_case(use_case_name=new_name, state=value)
            item.remove_use_case(old_name)

    def remove_project_phase(self, project_phase_name: str) -> None:
        if project_phase_name not in self._project_phases:
            return
        self._project_phases.remove(project_phase_name)

        for item in self.get_all_hirarchy_items():
            item.remove_project_phase(project_phase_name)

    def remove_use_case(self, use_case_name: str) -> None:
        if use_case_name not in self._use_cases:
            return
        self._use_cases.remove(use_case_name)

        for item in self.get_all_hirarchy_items():
            item.remove_use_case(use_case_name)

    @property
    def current_project_phase(self) -> str:
        if self._current_project_phase in self._project_phases:
            return self._current_project_phase
        else:
            logging.error(f"{self._current_project_phase} not in {self._project_phases}")

    @property
    def current_use_case(self) -> str:
        if self._current_use_case in self._use_cases:
            return self._current_use_case
        else:
            logging.error(f"{self._current_use_case} not in {self._use_cases}")

    @current_project_phase.setter
    def current_project_phase(self, value: str) -> None:
        if value in self._project_phases:
            self._current_project_phase = value
        else:
            logging.error(f"'{value}' nicht in Leistungsphasen-verzeichnis enthalten")

    @current_use_case.setter
    def current_use_case(self, value: str) -> None:
        if value in self._use_cases:
            self._current_use_case = value
        else:
            logging.error(f"'{value}' nicht in Anwendungsfall-verzeichnis enthalten")

    def create_mapping_script(self, pset_name: str, path: str) -> None:
        filehandling.create_mapping_script(self, pset_name, path)

    def open(self, path: str | os.PathLike) -> dict:
        json_dict = filehandling.import_json(self, path)
        return json_dict

    def save(self, path: str | os.PathLike) -> dict:
        json_dict = filehandling.export_json(self, path)
        return json_dict

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def author(self) -> str:
        return self._author

    @author.setter
    def author(self, value: str):
        self._author = value

    @property
    def version(self) -> str:
        return self._version

    @version.setter
    def version(self, value: str):
        self._version = value

    def clear(self):
        for obj in Object:
            obj.delete()
        for pset in PropertySet:
            pset.delete()

        for attribute in Attribute:
            attribute.delete()
        self.name = ""
        self.author = ""
        self.version = "1.0.0"
        self.name = ""

    @staticmethod
    def get_all_objects() -> Iterator[Object]:
        return iter(Object)

    def filter_by_project_phase(func):
        """decorator function that filters list output of function by project phase"""
        def inner(self):
            res = func(self)
            return list(filter(lambda obj: obj.get_project_phase_state(self.current_project_phase), res))

        return inner

    def filter_by_use_case(func):
        """decorator function that filters list output of function by use-case"""
        def inner(self):
            res = func(self)
            return list(filter(lambda obj: obj.get_use_case_state(self.current_use_case), res))

        return inner

    @property
    @filter_by_project_phase
    @filter_by_use_case
    def objects(self) -> list[Object]:
        objects: list[Object] = list(Object)
        return objects

    @staticmethod
    def get_all_aggregations() -> Iterator[Aggregation]:
        return iter(Aggregation)

    @property
    @filter_by_project_phase
    @filter_by_use_case
    def aggregations(self) -> list[Aggregation]:
        aggregations = list(Aggregation)
        return aggregations

    def tree(self) -> AnyNode:
        def create_childen(node: AnyNode):
            n_obj: Object = node.obj
            for child in n_obj.children:
                child_node = AnyNode(name=child.name, id=child.ident_value, obj=child, parent=node)
                create_childen(child_node)

        base = AnyNode(id=self.name, obj=self)
        root_objects = list()
        for obj in self.objects:
            if obj.parent is not None:
                continue
            root_objects.append(AnyNode(name=obj.name, id=obj.ident_value, obj=obj, parent=base))

        for n in root_objects:
            create_childen(n)
        return base


class Hirarchy(object, metaclass=IterRegistry):

    def __init__(self, name: str, description: str | None = None, optional: bool | None = None,
                 project: Project | None = None,
                 project_phase_dict: dict[str, bool] | None = None, use_case_dict: dict[str, bool] = None) -> None:
        self._project = project
        if project_phase_dict is None:
            project_phase_dict = dict()
        if use_case_dict is None:
            use_case_dict = dict()
        self._project_phase_dict: dict[str, bool] = project_phase_dict
        self._use_case_dict: dict[str, bool] = use_case_dict
        self._parent = None
        self._children = set()
        self._name = name
        self._mapping_dict = {
            value_constants.SHARED_PARAMETERS: True,
            json_constants.IFC_MAPPING:        True
        }
        self._description = ""
        if description is not None:
            self.description = description

        self._optional = False
        if optional is not None:
            self._optional = optional

    def _get_project(self, parent_element: Object | PropertySet) -> Project | None:
        if self._project is not None:
            return self._project

        if parent_element is not None:
            return parent_element.project
        return None

    def remove_parent(self) -> None:
        self._parent = None

    def get_project_phase_dict(self) -> dict[str, bool]:
        return dict(self._project_phase_dict)

    def get_use_case_dict(self) -> dict[str, bool]:
        return dict(self._use_case_dict)

    def get_project_phase_state(self, project_phase_name: str) -> bool:
        state = self._project_phase_dict.get(project_phase_name)
        if state is None:
            return True
        return state

    def get_use_case_state(self, use_case_name: str) -> bool:
        state = self._use_case_dict.get(use_case_name)
        state = True if state is None else state
        return state

    def remove_project_phase(self, project_phase_name: str) -> None:
        if project_phase_name in self._project_phase_dict:
            self._project_phase_dict.pop(project_phase_name)

    def remove_use_case(self, use_case_name: str) -> None:
        if use_case_name in self._project_phase_dict:
            self._project_phase_dict.pop(use_case_name)

    def add_project_phase(self, project_phase_name: str, state: bool) -> None:
        self._project_phase_dict[project_phase_name] = state

    def add_use_case(self, use_case_name: str, state: bool) -> None:
        self._use_case_dict[use_case_name] = state

    def set_project_phase(self, project_phase_name: str, state: bool) -> None:
        if project_phase_name in self._project_phase_dict:
            self._project_phase_dict[project_phase_name] = state
        else:
            self.add_project_phase(project_phase_name, state)

    def set_use_case(self, use_case_name: str, state: bool) -> None:
        if use_case_name in self._use_case_dict:
            self._use_case_dict[use_case_name] = state
        else:
            self.add_use_case(use_case_name, state)

    @property
    def optional_wo_hirarchy(self) -> bool:
        return self._optional

    @property
    def optional(self) -> bool:
        if self.parent is not None:
            if self.parent.optional:
                return True
        return self._optional

    @optional.setter
    def optional(self, value: bool) -> None:
        self._optional = value

    @property
    def description(self):
        if self.parent is None:
            return self._description
        if self._description:
            return self._description
        return self.parent.description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def mapping_dict(self) -> dict[str, bool]:
        return self._mapping_dict

    @mapping_dict.setter
    def mapping_dict(self, value: dict[str, bool]) -> None:
        self._mapping_dict = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        for child in self.children:
            child.name = value

    @property
    def parent(self) -> PropertySet | Object | Attribute | Aggregation:
        return self._parent

    @parent.setter
    def parent(self, parent: PropertySet | Object | Attribute | Aggregation) -> None:
        if self.parent is not None:
            self.parent._children.remove(self)
        self._parent = parent
        if parent is not None:
            self._parent._children.add(self)

    @property
    def is_parent(self) -> bool:
        if self.children:
            return True
        else:
            return False

    @property
    def is_child(self) -> bool:
        if self.parent is not None:
            return True
        else:
            return False

    @property
    def children(self) -> set[PropertySet | Object | Attribute | Aggregation]:
        return self._children

    def get_all_children(self):
        return self._children

    def add_child(self, child: PropertySet | Object | Attribute | Aggregation) -> None:
        self.children.add(child)
        child.parent = self

    def remove_child(self, child: PropertySet | Object | Attribute | Aggregation | Hirarchy) -> None:
        if child in self._children:
            self._children.remove(child)

    def delete(self, recursive: bool = False) -> None:
        logging.info(f"Delete {self.__class__.__name__} {self.name} (recursive: {recursive})")
        if self.parent is not None:
            self.parent.remove_child(self)

        if self in self._registry:
            self._registry.remove(self)

        if recursive:
            for child in list(self.children):
                child.delete(recursive)

        else:
            for child in self.children:
                child.remove_parent()
        del self


class Object(Hirarchy):
    _registry: set[Object] = set()

    def __init__(self, name: str, ident_attrib: [Attribute, str], uuid: str = None,
                 ifc_mapping: set[str] | None = None, description: None | str = None,
                 optional: None | bool = None, abbreviation: None | str = None, project: None | Project = None,
                 project_phases: None | dict[str, bool] = None, use_cases: None | dict[str, bool] = None) -> None:
        super(Object, self).__init__(name, description, optional, project, project_phases, use_cases)
        self._registry.add(self)
        self._property_sets: list[PropertySet] = list()
        self._ident_attrib = ident_attrib
        self._aggregations: set[Aggregation] = set()
        self.custom_attribues = {}

        self._abbreviation = abbreviation
        if abbreviation is None:
            self._abbreviation = ""

        self._ifc_mapping = ifc_mapping
        if ifc_mapping is None:
            self._ifc_mapping = {"IfcBuildingElementProxy"}

        self.uuid = uuid
        if uuid is None:
            self.uuid = str(uuid4())

    def __str__(self):
        return f"Object {self.name}"

    def __lt__(self, other: Object):
        return self.ident_value < other.ident_value

    def __copy__(self):
        new_ident_attribute = None
        if self.is_concept:
            ident_pset = None
            new_ident_attribute = str(self.ident_attrib)
        else:
            ident_pset = self.ident_attrib.property_set

        new_property_sets = set()
        for pset in self.property_sets:
            new_pset = cp.copy(pset)
            new_property_sets.add(new_pset)
            if pset == ident_pset:
                new_ident_attribute = new_pset.get_attribute_by_name(self.ident_attrib.name)

        if new_ident_attribute is None:
            raise ValueError(f"Identifier Attribute could'nt be found")

        new_object = Object(name=self.name, ident_attrib=new_ident_attribute, uuid=str(uuid4()),
                            ifc_mapping=self.ifc_mapping,
                            description=self.description, optional=self.optional, abbreviation=self.abbreviation,
                            project=self.project, project_phases=self.get_project_phase_dict(),
                            use_cases=self.get_use_case_dict())

        for pset in new_property_sets:
            new_object.add_property_set(pset)

        if self.parent is not None:
            self.parent.add_child(new_object)

        return new_object

    @property
    def project(self) -> Project | None:
        return self._project

    @property
    def abbreviation(self) -> str:
        return self._abbreviation

    @abbreviation.setter
    def abbreviation(self, value) -> None:
        self._abbreviation = value

    @property
    def ifc_mapping(self) -> set[str]:
        return self._ifc_mapping

    @ifc_mapping.setter
    def ifc_mapping(self, value: set[str]):
        value_set = set()
        for item in value:  # filter empty Inputs
            if not (item == "" or item is None):
                value_set.add(item)
        self._ifc_mapping = value_set

    def add_ifc_map(self, value: str) -> None:
        self._ifc_mapping.add(value)

    def remove_ifc_map(self, value: str) -> None:
        self._ifc_mapping.remove(value)

    @property
    def aggregations(self) -> set[Aggregation]:
        return self._aggregations

    def add_aggregation(self, node: Aggregation) -> None:
        self._aggregations.add(node)

    def remove_aggregation(self, node: Aggregation) -> None:
        self._aggregations.remove(node)

    @property
    def inherited_property_sets(self) -> dict[Object, list[PropertySet]]:
        def recursion(recursion_property_sets, recursion_obj: Object):
            psets = recursion_obj.property_sets

            if psets:
                recursion_property_sets[recursion_obj] = psets

            parent = recursion_obj.parent
            if parent is not None:
                recursion_property_sets = recursion(recursion_property_sets, parent)
            return recursion_property_sets

        property_sets = dict()
        if self.parent is not None:
            inherited_property_sets = recursion(property_sets, self.parent)
        else:
            inherited_property_sets = dict()

        return inherited_property_sets

    @property
    def is_concept(self) -> bool:
        if isinstance(self.ident_attrib, Attribute):
            return False
        else:
            return True

    @property
    def ident_attrib(self) -> Attribute | str:
        return self._ident_attrib

    @ident_attrib.setter
    def ident_attrib(self, value: Attribute) -> None:
        self._ident_attrib = value

    def get_all_property_sets(self) -> list[PropertySet]:
        """returns all Propertysets even if they don't fit the current Project Phase"""
        return self._property_sets

    @property
    def property_sets(self) -> list[PropertySet]:
        """returns PropertySets filtered by ProjectPhase
        -> If Project is not defined it returns all PropertySets"""
        if self.project is None:
            logging.warning(f"Project for Object {self} is not defined")
            property_sets = self.get_all_property_sets()
        else:
            property_sets = {pset for pset in self._property_sets if
                             pset.get_project_phase_state(self.project.current_project_phase)}
            property_sets = {p for p in property_sets if p.get_use_case_state(self.project.current_use_case)}
        return sorted(property_sets, key=lambda x: x.name)

    # override name setter because of intheritance
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    def add_property_set(self, property_set: PropertySet) -> None:
        self._property_sets.append(property_set)
        property_set.object = self

    def remove_property_set(self, property_set: PropertySet) -> None:
        if property_set in self._property_sets:
            self._property_sets.remove(property_set)

    def get_attributes(self, inherit: bool = False) -> list[Attribute]:
        attributes = list()
        for property_set in self.property_sets:
            attributes += property_set.attributes

        if inherit:
            attributes += self.parent.get_attributes(inherit=True)

        return attributes

    def delete(self, recursive: bool) -> None:
        super(Object, self).delete(recursive)

        for pset in self.property_sets:
            pset.delete(recursive, override_ident_deletion=True)

        for aggregation in self.aggregations.copy():
            aggregation.delete(recursive)

    def get_property_set_by_name(self, property_set_name: str) -> PropertySet | None:
        for property_set in self.property_sets:
            if property_set.name == property_set_name:
                return property_set
        return None

    @property
    def ident_value(self) -> str:
        if self.is_concept:
            return str()
        return ";".join(str(x) for x in self.ident_attrib.value)


class PropertySet(Hirarchy):
    _registry: set[PropertySet] = set()

    def __init__(self, name: str, obj: Object = None, uuid: str = None, description: None | str = None,
                 optional: None | bool = None, project: None | Project = None,
                 project_phases: None | dict[str, bool] = None, use_cases: None | dict[str, bool] = None) -> None:
        super(PropertySet, self).__init__(name, description, optional, project, project_phases, use_cases)
        self._attributes = set()
        self._object = None
        if obj is not None:
            obj.add_property_set(self)  # adds Pset to Object and sets pset.object = obj
        self._registry.add(self)
        self.uuid = uuid
        if self.uuid is None:
            self.uuid = str(uuid4())

    def __lt__(self, other):
        if isinstance(other, PropertySet):
            return self.name < other.name
        else:
            return self.name < other

    def __str__(self):
        return f"PropertySet: {self.name}"

    def __copy__(self) -> PropertySet:
        new_pset = PropertySet(name=self.name, obj=None, uuid=str(uuid4()), description=self.description,
                               optional=self.optional, project=self.project,
                               project_phases=self.get_project_phase_dict(), use_cases=self.get_use_case_dict())

        for attribute in self.attributes:
            new_attribute = cp.copy(attribute)
            new_pset.add_attribute(new_attribute)

        if self.parent is not None:
            self.parent.add_child(new_pset)

        return new_pset

    @property
    def is_predefined(self) -> bool:
        return self.object is None

    @property
    def parent(self) -> PropertySet:
        parent = super(PropertySet, self).parent
        return parent

    @parent.setter
    def parent(self, parent: PropertySet) -> None:
        if parent is None:
            self.remove_parent()
            return
        self._parent = parent

    def change_parent(self, new_parent: PropertySet) -> None:
        for attribute in self.attributes:
            if attribute.parent.property_set == self._parent:
                self.remove_attribute(attribute)
        self.parent = new_parent

    def delete(self, recursive: bool = False, override_ident_deletion=False) -> None:
        ident_attrib = None
        if self.object is not None:
            ident_attrib = self.object.ident_attrib

        if ident_attrib in self.attributes and not override_ident_deletion:
            logging.error(f"Can't delete Propertyset {self.name} because it countains the identifier Attribute")
            return

        super(PropertySet, self).delete()
        [attrib.delete(recursive) for attrib in self.attributes if attrib]
        if self.object is not None:
            self.object.remove_property_set(self)

    @property
    def project(self) -> Project | None:
        return self._get_project(self.object)

    @property
    def object(self) -> Object:
        return self._object

    @object.setter
    def object(self, value: Object):
        self._object = value

    def get_all_attributes(self) -> set[Attribute]:
        """returns all Attributes even if they don't fit the current Project Phase"""
        return self._attributes

    @property
    def attributes(self) -> set[Attribute]:
        """returns Attributes filtered by ProjectPhase
        -> If Project is not defined it returns all Attributes"""
        attributes = self.get_all_attributes()
        if self.project is not None:
            attributes = {attribute for attribute in attributes if
                          attribute.get_project_phase_state(self.project.current_project_phase)}
            attributes = {attribute for attribute in attributes if
                          attribute.get_use_case_state(self.project.current_use_case)}
        return attributes

    @attributes.setter
    def attributes(self, value: set[Attribute]) -> None:
        self._attributes = value

    def add_attribute(self, value: Attribute) -> None:
        if value.property_set is not None and value.property_set != self:
            value.property_set.remove_attribute(value)
        self._attributes.add(value)

        value.property_set = self
        for child in self.children:
            attrib: Attribute = cp.copy(value)
            value.add_child(attrib)
            child.add_attribute(attrib)

    def remove_attribute(self, value: Attribute, recursive=False) -> None:
        if value in self.attributes:
            self._attributes.remove(value)
            if recursive:
                for child in list(value.children):
                    child.property_set.remove_attribute(child)
        else:
            logging.warning(f"{self.name} -> {value} not in Attributes")

    def get_attribute_by_name(self, name: str):
        for attribute in self.attributes:
            if attribute.name.lower() == name.lower():
                return attribute
        return None

    def create_child(self, name) -> PropertySet:
        child = PropertySet(name=name, project=self.project)
        self.children.add(child)
        child.parent = self
        for attribute in self.attributes:
            new_attrib = attribute.create_child()
            child.add_attribute(new_attrib)
        return child


class Attribute(Hirarchy):
    _registry: set[Attribute] = set()

    def __init__(self, property_set: PropertySet | None, name: str, value: list, value_type: str,
                 data_type: str = value_constants.LABEL,
                 child_inherits_values: bool = False, uuid: str = None, description: None | str = None,
                 optional: None | bool = None, revit_mapping: None | str = None, project: Project | None = None,
                 project_phases: None | dict[str, bool] = None, use_cases: None | dict[str, bool] = None):

        super(Attribute, self).__init__(name, description, optional, project, project_phases, use_cases)
        self._value = value
        self._property_set = property_set
        self._value_type = value_type
        self._data_type = data_type
        self._registry.add(self)
        if revit_mapping is None:
            self._revit_name = name
        else:
            self._revit_name = revit_mapping

        self._child_inherits_values = child_inherits_values
        self.uuid = uuid

        if self.uuid is None:
            self.uuid = str(uuid4())
        if property_set is not None:
            property_set.add_attribute(self)

    def __str__(self) -> str:
        text = f"{self.property_set.name} : {self.name} = {self.value}"
        return text

    def __lt__(self, other):
        if isinstance(other, Attribute):
            return self.name < other.name
        else:
            return self.name < other

    def __copy__(self) -> Attribute:
        new_attrib = Attribute(property_set=None, name=self.name, value=cp.copy(self.value),
                               value_type=cp.copy(self.value_type),
                               data_type=cp.copy(self.data_type), child_inherits_values=self.child_inherits_values,
                               uuid=str(uuid4()),
                               description=self.description, optional=self.optional, revit_mapping=self.revit_name,
                               project=self.project, project_phases=self.get_project_phase_dict(),
                               use_cases=self.get_use_case_dict())

        if self.parent is not None:
            self.parent.add_child(new_attrib)
        return new_attrib

    def get_all_parents(self) -> list[Attribute]:
        parent = self.parent
        if parent is None:
            return []
        return parent.get_all_parents() + [parent]

    @property
    def project(self) -> Project | None:
        return self._get_project(self.property_set)

    @property
    def revit_name(self) -> str:
        return self._revit_name

    @revit_name.setter
    def revit_name(self, value: str) -> None:
        self._revit_name = value

    @property
    def child_inherits_values(self) -> bool:
        return self._child_inherits_values

    @child_inherits_values.setter
    def child_inherits_values(self, value: bool) -> None:
        self._child_inherits_values = value

    @property
    def name(self) -> str:
        return super(Attribute, self).name

    @name.setter
    def name(self, value: str) -> None:
        # ToDo: add request for unlink
        self._name = value
        for child in self.children:
            child.name = value

    @property
    def value(self) -> list:
        return self._value

    @value.setter
    def value(self, value: list) -> None:
        def can_be_changed() -> bool:
            change_bool = True
            if self.is_child:
                parent: Attribute = self.parent
                if parent.child_inherits_values:
                    change_bool = False
            return change_bool

        new_value = []

        for el in value:
            if isinstance(el, str):
                if "|" in el:
                    el = el.split("|")
                    for item in el:
                        new_value.append(item)
                else:
                    new_value.append(el)
            else:
                new_value.append(el)

        if can_be_changed():
            self._value = new_value

    @property
    def value_type(self) -> str:
        return self._value_type

    @value_type.setter
    def value_type(self, value: str):

        if not self.is_child:
            self._value_type = value

        if self.is_parent:
            for child in self.children:
                child._value_type = value

    @property
    def data_type(self) -> str:
        """
        IfcSimpleValue -> https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/
        :return:
        """

        return self._data_type

    @data_type.setter
    def data_type(self, value: str) -> None:
        if not self.is_child:
            self._data_type = value

        if self.is_parent:
            for child in self.children:
                child._data_type = value

    @property
    def property_set(self) -> PropertySet:
        return self._property_set

    @property_set.setter
    def property_set(self, value: PropertySet) -> None:
        self._property_set = value

    def is_equal(self, attribute: Attribute) -> bool:
        equal = True

        if self.name != attribute.name:
            equal = False

        if self.value != attribute.value:
            equal = False

        if self.property_set.name != attribute.property_set.name:
            equal = False

        if equal:
            return True
        else:
            return False

    def delete(self, recursive: bool) -> None:
        super(Attribute, self).delete(recursive)
        self.property_set.remove_attribute(self)

    def create_child(self) -> Attribute:
        child = cp.copy(self)
        self.add_child(child)
        return child


class Aggregation(Hirarchy):
    _registry: set[Aggregation] = set()

    def __str__(self):
        return self.name

    def __init__(self, obj: Object, parent_connection=value_constants.AGGREGATION, uuid: str | None = None,
                 description: None | str = None,
                 optional: None | bool = None, project_phases: None | dict[str, bool] = None,
                 use_cases: None | dict[str, bool] = None):
        super(Aggregation, self).__init__(obj.name, description, optional, project_phases, use_cases)
        self._registry.add(self)
        if uuid is None:
            self.uuid = str(uuid4())
        else:
            self.uuid = str(uuid)
        self.object = obj
        self._parent: Aggregation | None = None
        self._parent_connection = parent_connection
        self.object.add_aggregation(self)

    def delete(self, recursive: bool = False) -> None:
        super(Aggregation, self).delete(recursive)

        self.object.remove_aggregation(self)
        if not self.is_root:
            self.parent.remove_child(self)

    @property
    def project(self) -> Project | None:
        return self.object.project

    @property
    def parent_connection(self):
        if self.parent is None:
            return None
        return self._parent_connection

    @parent_connection.setter
    def parent_connection(self, value):
        self._parent_connection = value

    @property
    def parent(self) -> Aggregation:
        return self._parent

    def set_parent(self, value, connection_type):
        if self.parent is not None and value != self.parent:
            return False
        self._parent = value
        self._parent_connection = connection_type
        return True

    def remove_child(self, value: Aggregation):
        if value in self._children:
            self._children.remove(value)

    def add_child(self, child: Aggregation, connection_type: int = value_constants.AGGREGATION) -> bool:
        """returns if adding child is allowed"""

        def loop_parents(element, search_value):
            if element.parent is None:
                return True
            if element.parent.object == search_value:
                return False
            else:
                return loop_parents(element.parent, search_value)

        if child.object == self.object:
            return False

        if not loop_parents(self, child.object):
            return False

        if not child.set_parent(self, connection_type):
            return False

        self.children.add(child)
        child.parent_connection = connection_type
        return True

    @property
    def is_root(self):
        if self.parent is None:
            return True
        return False

    def id_group(self) -> str:
        abbrev_list = list()

        def iter_id(element: Aggregation):
            if element.parent_connection in (value_constants.AGGREGATION,
                                             value_constants.AGGREGATION + value_constants.INHERITANCE):
                abbrev_list.append(element.parent.object.abbreviation)
            if not element.is_root:
                iter_id(element.parent)

        if self.is_root:
            return ""

        iter_id(self)
        return "_xxx_".join(reversed(abbrev_list)) + "_xxx"

    def identity(self) -> str:
        return self.id_group() + "_" + self.object.abbreviation + "_xxx"


ClassTypes = Union[Project, Object, PropertySet, Attribute, Aggregation]
