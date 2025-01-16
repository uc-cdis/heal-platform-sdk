import json
from os import PathLike
from pathlib import Path
from typing import Dict

import jsonschema
from cdislogging import get_logger

from heal.vlmd.config import ALLOWED_SCHEMA_TYPES
from heal.vlmd.validate.utils import get_schema

logger = get_logger("json-validator", log_level="debug")


def read_data_from_json_file(input_file: str) -> Dict:
    """Loads the data from a json input file"""
    data = json.loads(Path(input_file).read_text())
    return data


def vlmd_validate_json(data_or_path, schema_type: str) -> bool:
    """
    Validate json file against specified schema type.

    Args:
        data_or_path: the path of the input HEAL VLMD file that to be validated
        schema_type (str): the type of the schema that can be validated against.
            Allowed values for now are “csv”, “tsv”, “json” and “auto”. Defaults to “auto”

    Returns:
        True for valid data and schema.
        Raises jsonschema.ValidationError if data is not valid
        or jsonschema.SchemaError if schema is not valid
    """

    if schema_type not in ALLOWED_SCHEMA_TYPES:
        raise ValueError(f"Schema type must be in {ALLOWED_SCHEMA_TYPES}")

    if isinstance(data_or_path, (str, PathLike)):
        logger.debug("Getting json data from file")
        data = read_data_from_json_file(data_or_path)
    else:
        logger.debug("Getting json data from object")
        data = data_or_path

    schema = get_schema(data_or_path, schema_type)
    if schema is None:
        raise ValueError(f"Could not get schema for type = {schema_type}")
    logger.debug("Checking schema")
    jsonschema.validators.Draft7Validator.check_schema(schema)

    logger.debug("Validating data")
    jsonschema.validate(instance=data, schema=schema)

    return True
