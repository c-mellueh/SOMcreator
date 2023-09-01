from __future__ import annotations

import copy
from typing import Iterator
from uuid import uuid4

from anytree import AnyNode

from . import constants, filehandling
from .external_software import excel


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

# Add child to Parent leads to reverse


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
        self._changed = True  # indecates if project was modified -> used for close dialog
        self.name = name
        self.aggregation_attribute = ""
        self.aggregation_pset = ""
        self.current_project_phase = 0

    def open(self, path) -> dict:
        json_dict = filehandling.import_json(self, path)
        return json_dict

    def save(self, path) -> dict:
        json_dict = filehandling.export_json(self, path)
        return json_dict

    @property
    def changed(self) -> bool:
        def check_data():
            for obj in Object:
                if obj.changed:
                    return True
            return False

        data = check_data()
        if data or self._changed:
            self._changed = True
        else:
            self._changed = False

        return self._changed

    @changed.setter
    def changed(self, value: bool) -> None:
        self._changed = value

    def reset_changed(self) -> None:
        for obj in Object:
            obj.changed = False
        self._changed = False

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        self._changed = True

    @property
    def author(self) -> str:
        return self._author

    @author.setter
    def author(self, value: str):
        self._author = value
        self._changed = True

    @property
    def version(self) -> str:
        return self._version

    @version.setter
    def version(self, value: str):
        self._version = value
        self._changed = True

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
        self.changed = True
        self.name = ""

    def import_excel(self, path: str, ws_name: str) -> None:
        excel.open_file(path, ws_name)

    @property
    def objects(self) -> Iterator[Object]:
        return iter(Object)

    @property
    def aggregations(self) -> Iterator[Aggregation]:
        return iter(Aggregation)

    def tree(self) -> AnyNode:
        def create_childen(node: AnyNode):
            obj: Object = node.obj
            for child in obj.children:
                child_node = AnyNode(id=child.name, obj=child, parent=node)
                create_childen(child_node)

        base = AnyNode(id=self.name, obj=self)
        root_objects = [AnyNode(id=obj.name, obj=obj, parent=base) for obj in Object if obj.parent is None]
        for n in root_objects:
            create_childen(n)
        return base

    def get_predefined_psets(self) -> set[PropertySet]:
        return set(pset for pset in PropertySet if pset.object == None)


class Hirarchy(object, metaclass=IterRegistry):

    def __init__(self, name: str, description: str | None = None, optional: bool | None = None,
                 project_phases: list[bool] | None = None) -> None:

        self.project_phases = project_phases
        self._parent = None
        self._children = set()
        self._name = name
        self.changed = True
        self._mapping_dict = {
            constants.SHARED_PARAMETERS: True,
            constants.IFC_MAPPING: True
        }
        self._description = ""
        if description is not None:
            self.description = description

        self._optional = False
        if optional is not None:
            self._optional = optional

        if self.project_phases is None:
            self.project_phases: list[bool] = [True for _ in range(9)]

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
        self.changed = True

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
        self.changed = True

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

    def add_child(self, child: PropertySet | Object | Attribute | Aggregation) -> None:
        self.children.add(child)
        child.parent = self
        self.changed = True

    def remove_child(self, child: PropertySet | Object | Attribute | Aggregation) -> None:
        self.children.remove(child)
        child.delete()

    def delete(self) -> None:
        if self in self._registry:
            self._registry.remove(self)


class PropertySet(Hirarchy):
    _registry: set[PropertySet] = set()

    def __init__(self, name: str, obj: Object = None, uuid: str = None, description: None | str = None,
                 optional: None | bool = None, project_phases: None| list[bool] = None) -> None:
        super(PropertySet, self).__init__(name, description, optional,project_phases)
        self._attributes = set()
        self._object = None
        if obj is not None:
            obj.add_property_set(self)  # adds Pset to Object and sets pset.object = obj
        self._registry.add(self)
        self.uuid = uuid
        if self.uuid is None:
            self.uuid = str(uuid4())
        self.changed = True

    def __lt__(self, other):
        if isinstance(other, PropertySet):
            return self.name < other.name
        else:
            return self.name < other

    @property
    def is_predefined(self) -> bool:
        if self.object is None:
            return True
        else:
            return False

    @property
    def parent(self) -> PropertySet:
        parent = super(PropertySet, self).parent
        return parent

    @parent.setter
    def parent(self, parent: PropertySet) -> None:
        if parent is None:
            self.remove_parent(self._parent)
            return
        self._parent = parent

    def change_parent(self, new_parent: PropertySet) -> None:
        for attribute in self.attributes:
            if attribute.parent.property_set == self._parent:
                self.remove_attribute(attribute)
        self.parent = new_parent

    def delete(self) -> None:
        super(PropertySet, self).delete()
        if self.object is not None:
            ident = self.object.ident_attrib  # if identifier in Pset delete all attributes except identifier
            if ident in self.attributes:
                remove_list = [attribute for attribute in self.attributes if attribute != ident]
                for attribute in remove_list:
                    self.remove_attribute(attribute)
            else:
                self.object.remove_property_set(self)

    @property
    def object(self) -> Object:
        return self._object

    @object.setter
    def object(self, value: Object):
        self._object = value
        self.changed = True

    @property
    def attributes(self) -> set[Attribute]:
        return self._attributes

    @attributes.setter
    def attributes(self, value: set[Attribute]) -> None:
        self._attributes = value
        self.changed = True

    def add_attribute(self, value: Attribute) -> None:
        self._attributes.add(value)
        self.changed = True

        # if value.property_set is not None:
        #     value.property_set.remove_attribute(value)
        value._property_set = self
        for child in self.children:
            attrib: Attribute = copy.copy(value)
            value.add_child(attrib)
            child.add_attribute(attrib)

    def remove_attribute(self, value: Attribute) -> None:
        if value in self.attributes:
            self.attributes.remove(value)
            for child in self.children:
                for attribute in list(child.attributes):
                    if attribute.parent == value:
                        child.remove_attribute(attribute)
            self.changed = True

    def get_attribute_by_name(self, name: str):
        for attribute in self.attributes:
            if attribute.name.lower() == name.lower():
                return attribute
        return None

    def remove_parent(self, old_parent: PropertySet):
        remove_list = list()
        for attribute in self.attributes:
            if attribute.parent.property_set == old_parent:
                remove_list.append(attribute)

        for attribute in remove_list:
            self.remove_attribute(attribute)
        self._parent = None

    def __copy__(self):
        new_pset = PropertySet(self.name)

        for attribute in self.attributes:
            new_attrib = copy.copy(attribute)
            new_pset.add_attribute(new_attrib)

        if self.parent is not None:
            self.parent.add_child(new_pset)

        return new_pset

    def create_child(self, name) -> PropertySet:
        child = PropertySet(name)
        self.children.add(child)
        child.parent = self
        for attribute in self.attributes:
            new_attrib = attribute.create_child()
            child.add_attribute(new_attrib)
        return child


class Attribute(Hirarchy):
    _registry: set[Attribute] = set()

    def __init__(self, property_set: PropertySet | None, name: str, value: list, value_type: int,
                 data_type: str = "xs:string",
                 child_inherits_values: bool = False, uuid: str = None, description: None | str = None,
                 optional: None | bool = None, revit_mapping: None | str = None, project_phases: None| list[bool] = None):

        super(Attribute, self).__init__(name, description, optional, project_phases)
        self._value = value
        self._property_set = property_set
        self._value_type = value_type
        self._data_type = data_type
        self._registry.add(self)
        if revit_mapping is None:
            self._revit_name = name
        else:
            self._revit_name = revit_mapping

        self.changed = True
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
        self.changed = True  # ToDo: add request for unlink
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
            self.changed = True

    @property
    def value_type(self) -> int:
        return self._value_type

    @value_type.setter
    def value_type(self, value: int):

        if not self.is_child:
            self._value_type = value
            self.changed = True

        if self.is_parent:
            for child in self.children:
                child._value_type = value
                self.changed = True

    @property
    def data_type(self) -> str:
        """
        "xs:string"; "xs:double"; "xs:boolean"; XS_INT = "xs:int"
        :return:
        """

        return self._data_type

    @data_type.setter
    def data_type(self, value: str) -> None:
        if not self.is_child:
            self._data_type = value
            self.changed = True

        if self.is_parent:
            for child in self.children:
                child._data_type = value
                self.changed = True

    @property
    def property_set(self) -> PropertySet:
        return self._property_set

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

    def delete(self) -> None:
        if self in self._registry:
            self._registry.remove(self)
        self.property_set.remove_attribute(self)
        for child in self.children:
            child.delete()

    def create_child(self) -> Attribute:
        child = copy.copy(self)
        self.add_child(child)
        return child

    def __copy__(self) -> Attribute:
        new_attrib: Attribute = Attribute(None, self.name, self.value,
                                          self.value_type, self.data_type, self.child_inherits_values)
        if self.parent is not None:
            self.parent.add_child(new_attrib)
        return new_attrib


class Object(Hirarchy):
    _registry: set[Object] = set()

    def __init__(self, name: str, ident_attrib: [Attribute, str], uuid: str = None,
                 ifc_mapping: set[str] | None = None, description: None | str = None,
                 optional: None | bool = None, abbreviation: None | str = None, project_phases: None| list[bool] = None) -> None:
        super(Object, self).__init__(name, description, optional,project_phases)
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

        self.changed = True

    def __str__(self):
        return f"Object {self.name}"

    def __lt__(self, other: Object):
        return self.ident_value < other.ident_value

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
        self.aggregations.remove(node)

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
    def ident_attrib(self) -> Attribute:
        return self._ident_attrib

    @ident_attrib.setter
    def ident_attrib(self, value: Attribute) -> None:
        self._ident_attrib = value
        self.changed = True

    @property
    def property_sets(self) -> list[PropertySet]:
        return self._property_sets

    # override name setter because of intheritance
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        self.changed = True

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

    def delete(self) -> None:
        Object._registry.remove(self)
        pset: PropertySet
        for pset in self.property_sets:
            pset.delete()

        for aggregation in self.aggregations.copy():
            aggregation.delete()

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


class Aggregation(Hirarchy):
    _registry: set[Aggregation] = set()

    def __str__(self):
        return self.name

    def __init__(self, obj: Object, parent_connection=constants.AGGREGATION, uuid: str | None = None,
                 description: None | str = None,
                 optional: None | bool = None,project_phases: None| list[bool] = None ):
        super(Aggregation, self).__init__(obj.name, description, optional,project_phases)
        self._registry.add(self)
        if uuid is None:
            self.uuid = str(uuid4())
        else:
            self.uuid = str(uuid)
        self.object = obj
        self._parent: Aggregation | None = None
        self._parent_connection = parent_connection
        self.object.add_aggregation(self)

    def delete(self) -> None:
        super(Aggregation, self).delete()
        self.object.remove_aggregation(self)
        if not self.is_root:
            self.parent.children.remove(self)
        for child in self.children:
            child.parent = None

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

    def remove_parent(self):
        self.parent.children.remove(self)
        self._parent = None

    def add_child(self, child: Aggregation, connection_type: int = constants.AGGREGATION) -> bool:
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
            if element.parent_connection in (constants.AGGREGATION, constants.AGGREGATION + constants.INHERITANCE):
                abbrev_list.append(element.parent.object.abbreviation)
            if not element.is_root:
                iter_id(element.parent)

        if self.is_root:
            return ""

        iter_id(self)
        return "_xxx_".join(reversed(abbrev_list)) + "_xxx"

    def identity(self) -> str:
        return self.id_group() + "_" + self.object.abbreviation + "_xxx"

