from typing import List, Optional, Union, Any, Dict

from reqif.models.reqif_types import SpecObjectAttributeType


class DefaultValueEmptySelfClosedTag:
    pass


class SpecAttributeDefinition:  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        xml_node: Optional[Any],
        attribute_type: SpecObjectAttributeType,
        description: Optional[str],
        identifier: str,
        last_change: Optional[str],
        datatype_definition: str,
        long_name: Optional[str],
        editable: Optional[bool],
        default_value: Union[None, DefaultValueEmptySelfClosedTag, str],
        multi_valued: Optional[bool],
    ):
        self.xml_node: Optional[Any] = xml_node
        self.attribute_type: SpecObjectAttributeType = attribute_type
        self.description: Optional[str] = description
        self.identifier: str = identifier
        self.last_change: Optional[str] = last_change
        self.datatype_definition: str = datatype_definition
        self.long_name: Optional[str] = long_name
        self.editable: Optional[bool] = (
            editable == "true" if editable is not None else None
        )
        self.default_value: Union[
            None, DefaultValueEmptySelfClosedTag, str
        ] = default_value
        self.multi_valued: Optional[bool] = multi_valued

    @staticmethod
    def create(
        attribute_type: SpecObjectAttributeType,
        identifier: str,
        datatype_definition: str,
        long_name: Optional[str] = None,
        multi_valued: Optional[bool] = None,
    ):
        return SpecAttributeDefinition(
            xml_node=None,
            attribute_type=attribute_type,
            description=None,
            identifier=identifier,
            last_change=None,
            datatype_definition=datatype_definition,
            long_name=long_name,
            editable=None,
            default_value=None,
            multi_valued=multi_valued,
        )

    def __str__(self) -> str:
        return (
            f"SpecAttributeDefinition("
            f"attribute_type={self.attribute_type}"
            ", "
            f"description={self.description}"
            ", "
            f"identifier={self.identifier}"
            ", "
            f"last_change={self.last_change}"
            ", "
            f"datatype_definition={self.datatype_definition}"
            ", "
            f"long_name={self.long_name}"
            ", "
            f"default_value={self.default_value}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()


class ReqIFSpecObjectType:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        description: Optional[str],
        identifier: str,
        last_change: Optional[str],
        long_name,
        attribute_definitions: Optional[List[SpecAttributeDefinition]],
        attribute_map: Optional[Dict[str, SpecAttributeDefinition]],
    ):
        self.description: Optional[str] = description
        self.identifier: str = identifier
        self.last_change: Optional[str] = last_change
        self.long_name = long_name
        self.attribute_definitions: Optional[
            List[SpecAttributeDefinition]
        ] = attribute_definitions
        self.attribute_map: Optional[
            Dict[str, SpecAttributeDefinition]
        ] = attribute_map

    @staticmethod
    def create(  # pylint: disable=too-many-arguments
        identifier: str,
        long_name: str,
        description: Optional[str] = None,
        last_change: Optional[str] = None,
        attribute_definitions: Optional[List[SpecAttributeDefinition]] = None,
        attribute_map: Optional[Dict[str, SpecAttributeDefinition]] = None,
    ):
        return ReqIFSpecObjectType(
            description=description,
            identifier=identifier,
            last_change=last_change,
            long_name=long_name,
            attribute_definitions=attribute_definitions,
            attribute_map=attribute_map,
        )

    def __str__(self) -> str:
        return (
            f"ReqIFSpecObjectType("
            f"description: {self.description}"
            ", "
            f"identifier: {self.identifier}"
            ", "
            f"last_change: {self.last_change}"
            ", "
            f"long_name: {self.long_name}"
            ", "
            f"attribute_definitions: {self.attribute_definitions}"
            ", "
            f"attribute_map: {self.attribute_map}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
