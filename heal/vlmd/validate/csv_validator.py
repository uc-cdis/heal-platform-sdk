import jsonschema

from cdislogging import get_logger
from heal.vlmd.config import ALLOWED_SCHEMA_TYPES
from heal.vlmd.utils import add_types_to_props
from heal.vlmd.validate.utils import get_schema, read_delim

logger = get_logger("csv-validator", log_level="debug")


def vlmd_validate_csv(data_or_path, schema_type: str) -> bool:
    """
    Validate CSV file against specified schema type.

    Args:
        data_or_path: input file path or json array of VLMD data to validate.
        schema_type (str): the type of the schema that can be validated against.
            Allowed values for now are “csv”, “tsv”, “json” and “auto”.

    Returns:
        True for valid data and schema.
        Raises jsonschema.ValidationError if data is not valid
        or jsonschema.SchemaError if schema is not valid
    """

    if schema_type not in ALLOWED_SCHEMA_TYPES:
        raise ValueError(f"Schema type must be in {ALLOWED_SCHEMA_TYPES}")

    if isinstance(data_or_path, list):
        logger.debug("Getting csv as json array from input object")
        data = data_or_path
    else:
        logger.debug("Getting csv data from file")
        data = read_delim(data_or_path).to_dict(orient="records")

    if len(data) == 0:
        raise ValueError(f"Could not read csv data from input")

    schema = get_schema(data_or_path, schema_type)
    if schema == None:
        raise ValueError(f"Could not get schema for type = {schema_type}")

    if isinstance(data_or_path, list):
        schema = schema["items"]
    schema = add_types_to_props(schema)
    logger.debug("Checking schema")
    jsonschema.validators.Draft7Validator.check_schema(schema)

    logger.debug("Validating data")
    jsonschema.validate(instance=data, schema=schema)

    return True
