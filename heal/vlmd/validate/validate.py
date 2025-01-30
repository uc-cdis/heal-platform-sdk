from os.path import isfile
from pathlib import Path

import jsonschema
from cdislogging import get_logger
from jsonschema import ValidationError

from heal.vlmd.config import (
    ALLOWED_INPUT_TYPES,
    ALLOWED_OUTPUT_TYPES,
    ALLOWED_SCHEMA_TYPES,
)
from heal.vlmd.extract.conversion import convert_to_vlmd
from heal.vlmd.utils import add_types_to_props
from heal.vlmd.validate.utils import get_schema, read_data_from_json_file, read_delim

logger = get_logger("vlmd-validate-extract", log_level="debug")


class ExtractionError(Exception):
    pass


file_type_to_fxn_map = {
    "csv": "csv-data-dict",
    "json": "json-template",
    "tsv": "csv-data-dict",
}


def vlmd_validate(
    input_file: str,
    schema_type="auto",
    output_type="json",
    return_converted_output=False,
):
    """
    Validates the input file against a VLMD schema.

    Args:

        input_file (str): the path of the input HEAL VLMD file.
        schema_type (str): the type of the schema to be validated against.
            Allowed values for now are “csv”, “tsv”, “json” and “auto”.
            Defaults to “auto” which will use the suffix of the input file.
        output_type (str): format of the converted dictionary: "csv" or "json.
            The default is "json".
        return_converted_output (bool): set to True to get converted output, else
            get a boolean for valid/invalid input.

    Returns:
        True if input is valid and return_converted_output=False.
        Returns a converted dictionary if input is valid and return_converted_output=True.
        Raises ValidationError if the input VLMD is not valid.
        Raises ValueError for unallowed input file types or unallowed schema types.
        Raises SchemaError if the schema is invalid.
        Raises ExctractionError if the input cannot be converted to VLMD dictionary.
    """

    logger.info(
        f"Validating VLMD file '{input_file}' against schema type '{schema_type}'"
    )
    file_suffix = Path(input_file).suffix.replace(".", "")
    if file_suffix not in ALLOWED_INPUT_TYPES:
        message = f"Input file must be one of {ALLOWED_INPUT_TYPES}"
        logger.error(message)
        raise ValueError(message)
    if not isfile(input_file):
        message = f"Input file does not exist: {input_file}"
        logger.error(message)
        raise IOError(message)

    if schema_type not in ALLOWED_SCHEMA_TYPES:
        message = f"Schema type must be in {ALLOWED_SCHEMA_TYPES}"
        logger.error(message)
        raise ValueError(message)
    schema = get_schema(input_file, schema_type)
    if schema is None:
        message = f"Could not get schema for type = {schema_type}"
        logger.error(message)
        raise ValueError(message)

    output_type = output_type if output_type else "json"
    if output_type not in ALLOWED_OUTPUT_TYPES:
        message = f"Unrecognized output_type '{output_type}' - should be in {ALLOWED_OUTPUT_TYPES}"
        logger.error(message)
        raise ValueError(message)

    # TODO: We need this for csv - see if we can add this to get_schema
    if file_suffix in ["csv", "tsv"]:
        schema = add_types_to_props(schema)
    logger.debug("Checking schema")
    jsonschema.validators.Draft7Validator.check_schema(schema)

    # read the input file
    if file_suffix in ["csv", "tsv"]:
        logger.debug("Getting csv data from file")
        data = read_delim(input_file).to_dict(orient="records")
        if len(data) == 0:
            message = "Could not read csv data from input"
            logger.error(message)
            raise ValidationError(message)
    elif file_suffix == "json":
        logger.debug("Getting json data from file")
        data = read_data_from_json_file(input_file)

    # if json then try a validation
    if file_suffix == "json":
        logger.debug("Validating json data")
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            logger.error("Error in validating json input")
            raise e

    # convert
    input_type = file_type_to_fxn_map.get(file_suffix)
    if not input_type:
        message = f"Could not get conversion function from file_suffix '{file_suffix}'"
        logger.error(message)
        raise ExtractionError(message)
    data_dictionaries = {}
    logger.debug(f"Verifying vlmd can be converted using input_type '{input_type}'")
    data_dictionary_props = {}
    try:
        data_dictionaries = convert_to_vlmd(
            input_filepath=input_file,
            input_type=input_type,
            data_dictionary_props=data_dictionary_props,
        )
    except Exception as e:
        logger.error(f"Error in converting dictionary from {input_file}")
        logger.error(e)
        raise ExtractionError(str(e))
    if output_type == "json":
        converted_dictionary = data_dictionaries["template_json"]
    elif output_type == "csv":
        converted_dictionary = data_dictionaries["template_csv"]["fields"]

    # get a new schema if the output_type is different than input file_type.
    if output_type != file_suffix and not (
        file_suffix == "tsv" and output_type == "csv"
    ):
        logger.debug(
            f"Getting schema for '{output_type}' to validate converted dictionary"
        )
        schema = get_schema(converted_dictionary, schema_type=output_type)
        if output_type == "csv":
            # TODO: see if we can add this to get_schema
            schema = add_types_to_props(schema)
        if schema is None:
            message = f"Could not get schema for type = {schema_type}"
            logger.error(message)
            raise ValueError(message)

    try:
        jsonschema.validate(instance=converted_dictionary, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error("Error in validating converted dictionary")
        raise e

    if return_converted_output:
        return converted_dictionary
    else:
        return True
