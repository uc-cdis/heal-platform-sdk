import jsonschema

from cdislogging import get_logger
from heal.vlmd.config import ALLOWED_SCHEMA_TYPES
from heal.vlmd.validate.utils import add_types_to_props, get_schema, read_delim

logger = get_logger("CSV_VALIDATOR", log_level="debug")


def vlmd_validate_csv(input_file: str, schema_type: str) -> bool:
    """
    Validate CSV file against specified schema type.

    Args:
        input_file (str): the path of the input HEAL VLMD file that to be validated
        schema_type (str): the type of the schema that can be validated against.
            Allowed values for now are “csv”, “tsv”, “json” and “auto”.

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

    schema = add_types_to_props(schema)
    logger.debug("Checking schema")
    jsonschema.validators.Draft7Validator.check_schema(schema)

    data = read_delim(input_file).to_dict(orient="records")
    if len(data) == 0:
        raise ValueError(f"Could not read data from file {input_file}")

    logger.debug("Validating data")
    jsonschema.validate(instance=data, schema=schema)

    return True
