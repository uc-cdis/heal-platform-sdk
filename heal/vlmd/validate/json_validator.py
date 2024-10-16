import json
from pathlib import Path
from typing import Dict

import jsonschema

from cdislogging import get_logger
from heal.vlmd.config import ALLOWED_SCHEMA_TYPES
from heal.vlmd.validate.utils import get_schema

logger = get_logger("JSON_VALIDATOR", log_level="debug")


def read_data_from_json_file(input_file: str) -> Dict:
    """Loads the data from a json input file"""
    data = json.loads(Path(input_file).read_text())
    return data


def vlmd_validate_json(input_file: str, schema_type: str) -> bool:
    """
    Validate json file against specified schema type.

    Args:
        input_file (str): the path of the input HEAL VLMD file that to be validated
        schema_type (str): the type of the schema that can be validated against.
            Allowed values for now are “csv”, “tsv”, “json” and “auto”. Defaults to “auto”

    Returns:
        True for valid data and schema.
        Raises jsonschema.ValidationError if data is not valid
        or jsonschema.SchemaError if schema is not valid
    """

    if schema_type not in ALLOWED_SCHEMA_TYPES:
        raise ValueError(f"Schema type must be in {ALLOWED_SCHEMA_TYPES}")

    schema = get_schema(input_file, schema_type)
    if schema == None:
        raise ValueError(f"Could not get schema for type = {schema_type}")
    logger.debug("Checking schema")
    jsonschema.validators.Draft7Validator.check_schema(schema)

    data = read_data_from_json_file(input_file)
    logger.debug("Validating data")
    jsonschema.validate(instance=data, schema=schema)

    return True
