import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from dataclasses_json import dataclass_json

from reqif.experimental.reqif_schema import ReqIFSchema
from reqif.models.reqif_data_type import (
    ReqIFDataTypeDefinitionDateIdentifier,
    ReqIFDataTypeDefinitionEnumeration,
    ReqIFDataTypeDefinitionString,
    ReqIFDataTypeDefinitionXHTML,
)
from reqif.models.reqif_spec_object import ReqIFSpecObject
from reqif.parser import ReqIFParser, ReqIFZParser
from reqif.reqif_bundle import ReqIFBundle, ReqIFZBundle


@dataclass_json
@dataclass
class Node:
    node_type: str
    level: int
    fields: Dict
    nodes: List["Node"] = field(default_factory=list)

    def get_as_dict(self):
        return self.to_dict()  # noqa: E1101

    def __str__(self):
        return f"Node(node_type = {self.node_type}, level = {self.level}, fields = {self.fields})"

    def __repr__(self):
        return self.__str__()


@dataclass_json
@dataclass
class Specification:
    # Some ReqIF documents may have no name.
    name: Optional[str]
    nodes: List[Node]

    @property
    def level(self):
        return 0

    def get_as_dict(self):
        return self.to_dict()  # noqa: E1101


@dataclass_json
@dataclass
class ReqDict:
    documents: List[Specification] = field(default_factory=list)
    fields: List = field(default_factory=list)

    def get_as_dict(self):
        return self.to_dict()  # noqa: E1101


class ReqIFToDictConverter:
    def __init__(self):
        pass

    @staticmethod
    def convert(reqif_bundle: ReqIFBundle) -> ReqDict:
        # This dictionary will be written to CSV.
        reqif_dict = ReqDict()

        reqif_schema = ReqIFSchema(reqif_bundle)

        # The easiest way to define the JSON/CSV columns is to collect all
        # field names available in the ReqIF file.
        # NOTE: This can create many unused columns if the requirements and
        # chapters attributes are two distinct sets of fields.
        reqif_dict.fields = []
        reqif_dict.fields.extend(
            map(
                lambda attribute_definition_:
                    {
                        "name": attribute_definition_.long_name,
                        "type": attribute_definition_.attribute_type.name
                    },
                reqif_schema.spec_object_type_attributes.values()
            )
        )

        assert (
            reqif_bundle.core_content.req_if_content.specifications is not None
        )
        for (
            specification
        ) in reqif_bundle.core_content.req_if_content.specifications:
            specification_dict: Specification = Specification(
                name=specification.long_name, nodes=[]
            )
            section_stack: List[Union[Specification, Node]] = [
                specification_dict
            ]

            for (
                current_hierarchy
            ) in reqif_bundle.iterate_specification_hierarchy(specification):
                spec_object = reqif_bundle.get_spec_object_by_ref(
                    current_hierarchy.spec_object
                )
                node: Node = ReqIFToDictConverter.convert_spec_object_to_node(
                    spec_object,
                    reqif_bundle,
                    reqif_schema,
                    current_hierarchy.level,
                )
                current_node = section_stack[-1]
                if not reqif_schema.is_spec_object_a_heading(spec_object):
                    if node.level > current_node.level:
                        assert node.level == (
                            current_node.level + 1
                        ), "Something went wrong with the spec hierarchy levels."
                        current_node.nodes.append(node)
                    elif node.level == current_node.level:
                        section_stack.pop()
                        current_node = section_stack[-1]
                        current_node.nodes.append(node)
                    else:
                        raise NotImplementedError
                else:
                    if node.level > current_node.level:
                        section_stack.append(node)
                        current_node.nodes.append(node)
                    elif node.level == current_node.level:
                        section_stack[-1] = node
                        current_node.nodes.append(node)
                    else:
                        while current_node.level >= node.level:
                            assert not isinstance(current_node, Specification)
                            section_stack.pop()
                            current_node = section_stack[-1]
                        section_stack.append(node)
                        current_node.nodes.append(node)

            reqif_dict.documents.append(specification_dict)

        return reqif_dict

    @staticmethod
    def convert_spec_object_to_node(
        spec_object: ReqIFSpecObject,
        reqif_bundle: ReqIFBundle,
        reqif_schema: ReqIFSchema,
        level,
    ):
        assert 1 <= level <= 10, "Expecting a reasonable level of nesting."
        spec_object_type_ref = spec_object.spec_object_type

        spec_object_type = reqif_bundle.get_spec_object_type_by_ref(
            spec_object_type_ref
        )
        assert spec_object_type is not None
        row_dict = {}
        for spec_object_attribute_ in spec_object.attributes:
            attribute_definition = reqif_schema.spec_object_type_attributes[
                spec_object_attribute_.definition_ref
            ]
            assert attribute_definition.long_name is not None

            data_type = reqif_schema.data_type_definitions[
                attribute_definition.datatype_definition
            ]
            assert data_type is not None
            if isinstance(data_type, ReqIFDataTypeDefinitionDateIdentifier):
                assert isinstance(spec_object_attribute_.value, str)
                row_dict[
                    attribute_definition.long_name
                ] = spec_object_attribute_.value
            elif isinstance(data_type, ReqIFDataTypeDefinitionEnumeration):
                assert isinstance(spec_object_attribute_.value, list)

                enum_values: List[str] = []
                for enum_value_identifier_ in spec_object_attribute_.value:
                    assert data_type.values is not None
                    for data_type_enum_value_ in data_type.values:
                        if (
                            data_type_enum_value_.identifier
                            == enum_value_identifier_
                        ):
                            assert data_type_enum_value_.long_name is not None
                            enum_values.append(data_type_enum_value_.long_name)
                            break
                    else:
                        raise AssertionError("Enum value not found.")
                row_dict[attribute_definition.long_name] = ", ".join(
                    enum_values
                )
            elif isinstance(data_type, ReqIFDataTypeDefinitionString):
                assert isinstance(spec_object_attribute_.value, str)
                row_dict[
                    attribute_definition.long_name
                ] = spec_object_attribute_.value
            elif isinstance(data_type, ReqIFDataTypeDefinitionXHTML):
                assert isinstance(spec_object_attribute_.value, str)
                row_dict[
                    attribute_definition.long_name
                ] = spec_object_attribute_.value
            else:
                raise NotImplementedError(data_type)

        node_type = reqif_schema.spec_object_type_names[
            spec_object_type.identifier
        ]
        return Node(node_type=node_type, level=level, fields=row_dict)


def main():
    main_parser = argparse.ArgumentParser()

    main_parser.add_argument(
        "input_file", type=str, help="Path to the input ReqIF file."
    )
    main_parser.add_argument(
        "--output-dir",
        type=str,
        help="Path to the output dir.",
        default="output/",
    )
    main_parser.add_argument(
        "--stdout",
        help="Makes the script write the output ReqIF to standard output.",
        action="store_true",
    )
    main_parser.add_argument(
        "--no-filesystem",
        help=(
            "Disables writing to the file system. "
            "Should be used in combination with --stdout."
        ),
        action="store_true",
    )

    args = main_parser.parse_args()
    input_file: str = args.input_file
    input_file_name = Path(input_file).stem
    should_use_file_system: bool = not args.no_filesystem
    should_use_stdout: bool = args.stdout

    if input_file.endswith(".reqifz"):
        reqifz_bundle: ReqIFZBundle = ReqIFZParser.parse(input_file)
        assert len(reqifz_bundle.reqif_bundles) == 1
        reqif_filename = next(iter(reqifz_bundle.reqif_bundles.keys()))
        input_file_name = reqif_filename
        reqif_bundle = reqifz_bundle.reqif_bundles[reqif_filename]
    else:
        reqif_bundle = ReqIFParser.parse(input_file)

    req_dict = ReqIFToDictConverter.convert(reqif_bundle)
    reqif_json = json.dumps(req_dict.get_as_dict(), indent=4)

    if should_use_file_system:
        path_to_output_dir = args.output_dir
        Path(path_to_output_dir).mkdir(exist_ok=True)

        path_to_output_file = os.path.join(
            path_to_output_dir, f"{input_file_name}.json"
        )
        with open(path_to_output_file, "w", encoding="utf8") as json_file:
            json_file.write(reqif_json)
            json_file.write("\n")

    if should_use_stdout:
        print(reqif_json)  # noqa: T201


main()
