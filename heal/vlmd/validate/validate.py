from os.path import isfile
from pathlib import Path

from jsonschema import ValidationError

from cdislogging import get_logger
from heal.vlmd.config import ALLOWED_INPUT_TYPES, ALLOWED_SCHEMA_TYPES
from heal.vlmd.validate.csv_validator import vlmd_validate_csv
from heal.vlmd.validate.json_validator import vlmd_validate_json

logger = get_logger("VALIDATE", log_level="debug")


def vlmd_validate(input_file: str, schema_type="auto") -> bool:
    """
    Validates the input file against a VLMD schema.

    Args:

        input_file (str): the path of the input HEAL VLMD file that to be validated
        schema_type (str): the type of the schema to be validated against.
            Allowed values for now are “csv”, “tsv”, “json” and “auto”.
            Defaults to “auto”.

    Returns:
        True if input is valid.
        Raises ValidationError if input VLMD is not valid.
        Raises ValueError for unallowed input file types or unallowed schema types.
        Raises SchemaError if schema is invalid.
    """

    logger.info(
        f"Validating VLMD file '{input_file}' against shema type '{schema_type}'"
    )

    if schema_type not in ALLOWED_SCHEMA_TYPES:
        raise ValueError(f"Schema type must be in {ALLOWED_SCHEMA_TYPES}")

    file_suffix = Path(input_file).suffix.replace(".", "")
    if file_suffix not in ALLOWED_INPUT_TYPES:
        raise ValueError(f"Input file must be one of {ALLOWED_INPUT_TYPES}")
    if not isfile(input_file):
        raise IOError(f"Input file does not exist: {input_file}")

    # TODO: could change to match-case if python is upgraded to 3.10
    if file_suffix == "csv" or file_suffix == "tsv":
        vlmd_validate_csv(input_file, schema_type)
    elif file_suffix == "json":
        vlmd_validate_json(input_file, schema_type)
    else:
        raise ValueError(f"Not able to handle file of type {file_suffix}")

    return True
