import os
import sys
from typing import List

from reqif.cli.cli_arg_parser import ValidateCommandConfig
from reqif.models.error_handling import (
    ReqIFSchemaError,
    ReqIFSpecRelationMissingSpecObjectException,
    ReqIFSemanticError,
    ReqIFGeneralSemanticError,
)
from reqif.models.reqif_spec_relation import ReqIFSpecRelation
from reqif.parser import ReqIFParser
from reqif.reqif_bundle import ReqIFBundle


class ReqIFErrorBundle:
    def __init__(
        self,
        schema_errors: List[Exception],
        semantic_warnings: List[ReqIFSemanticError],
    ):
        self.schema_errors: List[ReqIFSchemaError] = schema_errors
        self.semantic_warnings: List[ReqIFSemanticError] = semantic_warnings


class ValidateCommand:
    @classmethod
    def execute(cls, config: ValidateCommandConfig):
        input_file = config.input_file
        if not os.path.isfile(input_file):
            sys.stdout.flush()
            message = "error: passthrough command's input file does not exist"
            print(f"{message}: {input_file}")
            sys.exit(1)

        error_bundle = ValidateCommand._validate(config)
        for warning in error_bundle.schema_errors:
            print(f"warning: {warning.get_description()}")
        for warning in error_bundle.semantic_warnings:
            print(f"warning: semantic error: {warning.get_description()}")
        print(
            f"Validation complete with 0 errors, "
            f"{len(error_bundle.schema_errors)} schema issues found, "
            f"{len(error_bundle.semantic_warnings)} semantic issues found."
        )

    @staticmethod
    def _validate(
        passthrough_config: ValidateCommandConfig,
    ) -> ReqIFErrorBundle:
        semantic_warnings: List[ReqIFSemanticError] = []
        reqif_bundle = ReqIFParser.parse(passthrough_config.input_file)
        if not reqif_bundle.namespace_info.doctype_is_present:
            warning = ReqIFGeneralSemanticError(
                "Document is missing a valid XML declaration. Every ReqIF"
                "document should have the following line: "
                '<?xml version="1.0" encoding="UTF-8"?>'
            )
            semantic_warnings.append(warning)
        if reqif_bundle.namespace_info.encoding != "UTF-8":
            warning = ReqIFGeneralSemanticError(
                "ReqIF Implementation Guide recommends using UTF-8 "
                "encoding for ReqIF files. Every ReqIF "
                "document should have the following line: "
                '<?xml version="1.0" encoding="UTF-8"?>'
            )
            semantic_warnings.append(warning)

        core_content = reqif_bundle.core_content
        if core_content is not None:
            req_if_content = core_content.req_if_content
            if req_if_content is not None:
                spec_relations = req_if_content.spec_relations
                if spec_relations is not None:
                    spec_relation_semantic_errors = (
                        ValidateCommand._validate_spec_relations(
                            spec_relations=spec_relations,
                            reqif_bundle=reqif_bundle,
                        )
                    )
                    semantic_warnings.extend(spec_relation_semantic_errors)

        return ReqIFErrorBundle(
            schema_errors=reqif_bundle.exceptions,
            semantic_warnings=semantic_warnings,
        )

    @staticmethod
    def _validate_spec_relations(
        spec_relations: List[ReqIFSpecRelation],
        reqif_bundle: ReqIFBundle,
    ) -> List[ReqIFSemanticError]:
        semantic_errors = []
        for spec_relation in spec_relations:
            if not reqif_bundle.lookup.spec_object_exists(spec_relation.source):
                error = ReqIFSpecRelationMissingSpecObjectException(
                    xml_node=spec_relation.xml_node,
                    tag="SOURCE",
                    spec_object_identifier=spec_relation.source,
                )
                semantic_errors.append(error)
            if not reqif_bundle.lookup.spec_object_exists(spec_relation.target):
                error = ReqIFSpecRelationMissingSpecObjectException(
                    xml_node=spec_relation.xml_node,
                    tag="TARGET",
                    spec_object_identifier=spec_relation.target,
                )
                semantic_errors.append(error)
        return semantic_errors
