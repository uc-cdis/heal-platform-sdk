import jsonschema

from cdislogging import get_logger
from heal.vlmd.config import ALLOWED_SCHEMA_TYPES
from heal.vlmd.extract.conversion import convert_to_vlmd
from heal.vlmd.utils import add_types_to_props
from heal.vlmd.validate.json_validator import vlmd_validate_json
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
        from_file = False
    else:
        logger.debug("Getting csv data from file")
        data = read_delim(data_or_path).to_dict(orient="records")
        from_file = True

    if len(data) == 0:
        raise ValueError(f"Could not read csv data from input")

    schema = get_schema(data_or_path, schema_type)
    if schema == None:
        raise ValueError(f"Could not get schema for type = {schema_type}")

    schema = add_types_to_props(schema)
    logger.debug("Checking schema")
    jsonschema.validators.Draft7Validator.check_schema(schema)

    logger.debug("Validating data")
    logger.debug(data)
    # jsonschema.validate(instance=data, schema=schema)

    # any input that is an array is already converted from csv.
    if isinstance(data, list) and not from_file:
        logger.debug("Validating data")
        logger.debug(data)
        # Need to wrap in try
        jsonschema.validate(instance=data, schema=schema)
        logger.debug("No further validation, this is converted from CSV")
        return True

    # try conversion of input csv
    data_dictionaries = {}
    if from_file:
        logger.debug("Verifying vlmd can be converted")
        data_dictionary_props = {}
        input_type = "csv-data-dict"
        try:
            data_dictionaries = convert_to_vlmd(
                input_filepath=data_or_path,
                input_type=input_type,
                data_dictionary_props=data_dictionary_props,
            )
        except Exception as e:
            if from_file:
                logger.error(f"Error in converting dictionary from {data_or_path}")
            else:
                logger.error("Error in converting dictionary from json array input")
            logger.error(e)
            raise jsonschema.ValidationError(str(e))

    # now validate the converted dictionary
    converted_dictionary = data_dictionaries["templatejson"]
    try:
        vlmd_validate_json(converted_dictionary, schema_type="json")
    except jsonschema.ValidationError as e:
        logger.error("Error in validating converted dictionary")
        raise e

    return True
