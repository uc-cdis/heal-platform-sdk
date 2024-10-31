from os.path import isfile
from pathlib import Path

from jsonschema import ValidationError

from cdislogging import get_logger
from heal.vlmd.config import ALLOWED_INPUT_TYPES, ALLOWED_FILE_TYPES
from heal.vlmd.file_utils import get_output_filepath, write_vlmd_dict
from heal.vlmd.extract.conversion import convert_to_vlmd
from heal.vlmd import vlmd_validate
from heal.vlmd.validate.csv_validator import vlmd_validate_csv
from heal.vlmd.validate.json_validator import vlmd_validate_json

logger = get_logger("extract", log_level="debug")


class ExtractionError(Exception):
    pass


file_type_to_fxn_map = {
    "csv": "csv-data-dict",
    "json": "json-template",
    "tsv": "csv-data-dict",
}


def vlmd_extract(input_file, file_type="auto", output_dir=".", output_type="json"):
    """
    Extract a HEAL compliant csv and json format VLMD data dictionary
    from the input file.

    Args:
        input_file (str): the path of the input HEAL VLMD file to be extracted
            into HEAL-compliant VLMD file(s).
        file_type (str): the type of the input file that will be extracted into a
            HEAL-compliant VLMD file.
            Allowed values for now are "auto", “csv”, "json", "tsv",
            where the input files are VLMD.
            Defaults to “auto”
        output_dir (str): the directory of where the extracted VLMD file will
            be written. Defaults to “.”
        output_type (str): format of dictionary to write: "csv" or "json".
            The default is "json".

    Returns:
        True if the input is valid and is successfully converted and written.
        Raises ValidationError if input VLMD or converted VLMD is not valid.
        Raises ExtractionError for any other errors.
    """

    logger.info(f"Extracting VLMD file '{input_file}' with file_type '{file_type}'")

    file_suffix = Path(input_file).suffix.replace(".", "")
    if file_suffix not in ALLOWED_INPUT_TYPES:
        raise ExtractionError(f"Input file must be one of {ALLOWED_INPUT_TYPES}")
    if not isfile(input_file):
        raise ExtractionError(f"Input file does not exist: {input_file}")

    if file_type not in ALLOWED_FILE_TYPES:
        raise ExtractionError(f"File type must be one of {ALLOWED_FILE_TYPES}")
    if file_type == "auto":
        file_type = file_suffix

    input_type = file_type_to_fxn_map.get(file_type)
    if not input_type:
        raise ExtractionError(
            f"Could not get conversion function from file_type {file_type}"
        )

    if output_type not in ["csv", "json"]:
        raise ExtractionError(
            f"Unrecognized output_type '{output_type}' - should be 'csv' or 'json'"
        )

    logger.debug("Validating input file")
    try:
        vlmd_validate(input_file)
    except ValidationError as e:
        logger.error(f"Exception in validating input file {input_file}")
        logger.error(e)
        raise e

    # extract
    logger.debug("Ready to extract to vlmd")
    data_dictionary_props = {}
    try:
        data_dictionaries = convert_to_vlmd(
            input_filepath=input_file,
            input_type=input_type,
            data_dictionary_props=data_dictionary_props,
        )
    except Exception as e:
        logger.error(f"Error in extracting dictionary from {input_file}")
        logger.error(e)
        raise ExtractionError(f"Error in extracting dictionary from {input_file}")

    logger.debug(f"Got dictionaries with keys {data_dictionaries.keys()}")

    if output_type == "csv":
        converted_dictionary = data_dictionaries["templatecsv"]["fields"]
    if output_type == "json":
        converted_dictionary = data_dictionaries["templatejson"]

    try:
        if output_type == "csv":
            vlmd_validate_csv(converted_dictionary, schema_type="csv")
        if output_type == "json":
            vlmd_validate_json(converted_dictionary, schema_type="json")
    except ValidationError as e:
        logger.error(f"Error in validating converted {output_type}")
        raise e

    output_filepath = get_output_filepath(
        output_dir, input_file, output_type=output_type
    )
    logger.info(f"Writing converted dictionary to {output_filepath}")
    try:
        write_vlmd_dict(converted_dictionary, output_filepath, file_type=output_type)
    except Exception as e:
        logger.error(f"Error in writing converted dictionary")
        logger.error(e)
        raise ExtractionError(f"Error in writing converted dictionary")

    return True
