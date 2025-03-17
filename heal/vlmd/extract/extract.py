from os.path import isfile
from pathlib import Path
import re

from cdislogging import get_logger
from jsonschema import ValidationError

from heal.vlmd import ExtractionError, vlmd_validate
from heal.vlmd.config import (
    ALLOWED_FILE_TYPES,
    ALLOWED_INPUT_TYPES,
    ALLOWED_OUTPUT_TYPES,
    TOP_LEVEL_PROPS,
)
from heal.vlmd.extract.conversion import convert_to_vlmd
from heal.vlmd.file_utils import get_output_filepath, write_vlmd_dict
from heal.vlmd.validate.validate import file_type_to_fxn_map


logger = get_logger("extract", log_level="debug")


def set_title_if_missing(file_type: str, title: str, converted_dict: dict) -> dict:
    """
    Dictionary from json input should have an existing title or a user-supplied title.
    Dictionary from non-json input should set the title from
    standardsMappings[0].instrument.title or from the user supplied title.
    """

    existing_title = converted_dict.get("title")
    default_csv_title = TOP_LEVEL_PROPS.get("title")

    if file_type == "json":
        if existing_title is not None and existing_title != default_csv_title:
            logger.info(f"Converted dict already has a title {existing_title}")
            return converted_dict

        if title is not None:
            logger.debug(f"JSON dictionary setting user-defined title '{title}'")
            converted_dict["title"] = title
            return converted_dict

    else:
        instrument_title = None
        try:
            standards_mappings = converted_dict.get("standardsMappings")
            if standards_mappings and len(standards_mappings) >= 1:
                instrument_title = standards_mappings[0].get("instrument").get("title")
        except Exception as err:
            logger.warning("standardsMapping does not have 'instrument.title'")

        if title is None and instrument_title is None:
            message = "Title must be supplied when extracting from non-json to json"
            logger.error(message)
            raise ExtractionError(message)

        if instrument_title is not None:
            logger.debug(
                f"Converted CSV dictionary setting title to instrument title '{instrument_title}'"
            )
            converted_dict["title"] = instrument_title
            return converted_dict

        if title is not None and (
            existing_title is None or existing_title == default_csv_title
        ):
            logger.debug(
                f"Converted CSVdictionary setting user-defined title '{title}'"
            )
            converted_dict["title"] = title
            return converted_dict

    return converted_dict


def vlmd_extract(
    input_file, title=None, file_type="auto", output_dir=".", output_type="json"
) -> bool:
    """
    Extract a HEAL compliant csv and json format VLMD data dictionary
    from the input file.

    Args:
        input_file (str): the path of the input HEAL VLMD file to be extracted
            into HEAL-compliant VLMD file(s).
        title (str): the root level title of the dictionary (required if extracting from csv to json)
        file_type (str): the type of the input file that will be extracted into a
            HEAL-compliant VLMD file.
            Allowed values are "auto", “csv”, "json", "tsv", and "redcap"
            where "redcap" is a csv file of a REDCap dictionary export.
            Defaults to “auto”.
        output_dir (str): the directory of where the extracted VLMD file will
            be written. Defaults to “.”
        output_type (str): format of dictionary to write: "csv" or "json".
            The default is "json".

    Returns:
        True if the input is valid and is successfully converted and written.
        Raises ExtractionError in input VLMD is not valid or could not be converted.
    """

    logger.info(
        f"Extracting VLMD file '{input_file}' with input file_type '{file_type}'"
    )

    file_suffix = Path(input_file).suffix.replace(".", "")
    if file_suffix not in ALLOWED_INPUT_TYPES:
        message = f"Input file must be one of {ALLOWED_INPUT_TYPES}"
        logger.error(message)
        raise ExtractionError(message)

    if not isfile(input_file):
        message = f"Input file does not exist: {input_file}"
        logger.error(message)
        raise ExtractionError(message)

    if file_type not in ALLOWED_FILE_TYPES:
        message = f"File type must be one of {ALLOWED_FILE_TYPES}"
        logger.error(message)
        raise ExtractionError(message)

    if file_type == "auto":
        file_type = file_suffix

    if output_type not in ALLOWED_OUTPUT_TYPES:
        message = f"Unrecognized output_type '{output_type}' - should be in {ALLOWED_OUTPUT_TYPES}"
        logger.error(message)
        raise ExtractionError(message)

    if title is not None and re.match(r"^\s*$", title):
        message = f"Empty title is not allowed"
        logger.error(message)
        raise ExtractionError(message)

    logger.debug(f"File type is set to '{file_type}'")
    # validate
    try:
        # csv files are converted as part of validate
        converted_dictionary = vlmd_validate(
            input_file,
            file_type=file_type,
            output_type=output_type,
            return_converted_output=True,
        )
    except ValidationError as err:
        logger.error(f"Error in validating and extracting dictionary from {input_file}")
        logger.error(err.message)
        raise ExtractionError(str(err.message))
    except Exception as err:
        logger.error(f"Error in extracting dictionary from {input_file}")
        logger.error(err)
        raise ExtractionError(str(err))

    # input json file require explicit conversion and post validation steps
    if file_type == "json":
        file_convert_function = file_type_to_fxn_map.get(file_type)
        data_dictionary_props = {}
        try:
            logger.debug("Ready to convert json input to VLMD")
            data_dictionaries = convert_to_vlmd(
                input_filepath=input_file,
                input_type=file_convert_function,
                data_dictionary_props=data_dictionary_props,
            )
            if output_type == "json":
                converted_dictionary = data_dictionaries["template_json"]
                logger.debug(
                    f"Ready to validate converted dict with output type '{output_type}'"
                )
                is_valid = vlmd_validate(
                    converted_dictionary,
                    file_type=file_type,
                    output_type=output_type,
                    return_converted_output=False,
                )
                logger.debug(f"Converted dictionary is valid: {is_valid}")
            else:
                converted_dictionary = data_dictionaries["template_csv"]["fields"]
        except Exception as err:
            logger.error(f"Error in extracting JSON dictionary from {input_file}")
            logger.error(err)
            raise ExtractionError(str(err))

    if output_type == "json":
        converted_dictionary = set_title_if_missing(
            file_type=file_type, title=title, converted_dict=converted_dictionary
        )
        if converted_dictionary.get("title") is None:
            logger.error("JSON dictionary is missing 'title'")
            raise ExtractionError("JSON dictionary is missing 'title'")

    # write to file
    output_filepath = get_output_filepath(
        output_dir, input_file, output_type=output_type
    )
    logger.info(f"Writing converted dictionary to {output_filepath}")
    try:
        write_vlmd_dict(converted_dictionary, output_filepath, file_type=output_type)
    except Exception as err:
        logger.error("Error in writing converted dictionary")
        logger.error(err)
        raise ExtractionError("Error in writing converted dictionary")

    return True
