import re
from os.path import isfile
from pathlib import Path

import jsonschema
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
from heal.vlmd.extract.csv_dict_conversion import RedcapExtractionError
from heal.vlmd.file_utils import get_output_filepath, write_vlmd_dict
from heal.vlmd.validate.validate import file_type_to_fxn_map
from heal.vlmd.utils import add_types_to_props
from heal.vlmd.validate.utils import get_schema


logger = get_logger("extract", log_level="info")


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
            logger.info(f"Converted dict already has a title '{existing_title}'")
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
                f"Converted CSV dictionary setting user-defined title '{title}'"
            )
            converted_dict["title"] = title
            return converted_dict

    return converted_dict


def vlmd_extract(
    input_file: str,
    title: str = None,
    file_type: str = "auto",
    output_dir: str = ".",
    output_type: str = "json",
    include_all_fields: bool = True,
) -> bool:
    """
    Extract a HEAL compliant csv and json format VLMD data dictionary
    from the input file.

    Args:
        input_file (str): the path of the input HEAL VLMD file to be extracted
            into HEAL-compliant VLMD file(s).
        title (str): the root level title of the dictionary (required if extracting
            from csv to json)
        file_type (str): the type of the input file that will be extracted into a
            HEAL-compliant VLMD file.
            Allowed values are "auto", “csv”, "dataset_csv", "dataset_tsv",
                "json", "tsv", and "redcap".
            where "redcap" is a csv file of a REDCap dictionary export.
            Defaults to “auto”.
        output_dir (str): the directory of where the extracted VLMD file will
            be written. Defaults to “.”
        output_type (str): format of dictionary to write: "csv" or "json".
            The default is "json".
        include_all_fields (bool): If true then csv dictionaries extracted from
            csv datasets will include columns for all fields in the schema.
            Useful for generating a template that can be manually updated.
            Default = True.

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

    type_is_auto = False
    if file_type == "auto":
        # Set as data dictionary
        file_type = file_suffix
        logger.debug(f"Changing file_type from 'auto' to '{file_type}'")
        type_is_auto = True

    if output_type not in ALLOWED_OUTPUT_TYPES:
        message = f"Unrecognized output_type '{output_type}' - should be in {ALLOWED_OUTPUT_TYPES}"
        logger.error(message)
        raise ExtractionError(message)

    if title is not None and re.match(r"^\s*$", title):
        message = f"Empty title is not allowed"
        logger.error(message)
        raise ExtractionError(message)

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

    elif file_type in ["csv", "redcap", "tsv"]:
        try:
            # csv files are converted as part of validate
            converted_dictionary = vlmd_validate(
                input_file,
                file_type=file_type,
                output_type=output_type,
                return_converted_output=True,
            )
        except RedcapExtractionError as err:
            logger.error("Error in extracting REDCap dictionary")
            if type_is_auto:
                logger.info(
                    "File_type was 'auto' but input identified as REDCap. Skipping fallback to dataset."
                )
            raise ExtractionError(str(err))
        except ValidationError as err:
            logger.error(
                f"Error in validating and extracting dictionary from {input_file}"
            )
            logger.error(err.message)
            if type_is_auto:
                file_type = f"dataset_{file_suffix}"
                logger.info(
                    f"Will now attempt to extract file '{input_file}' as '{file_type}'"
                )
            else:
                raise ExtractionError(str(err.message))
        except Exception as err:
            logger.error(f"Error in extracting dictionary from {input_file}")
            logger.error(err)
            if type_is_auto:
                file_type = f"dataset_{file_suffix}"
                logger.info(
                    f"Will attempt to extract file '{input_file}' as '{file_type}'"
                )
            else:
                raise ExtractionError(str(err))

    # If data file then try conversion
    if file_type in ["dataset_csv", "dataset_tsv"]:
        file_convert_function = file_type_to_fxn_map.get(file_type)
        data_dictionary_props = {}
        try:
            logger.debug("Ready to convert csv data set input to VLMD")
            data_dictionaries = convert_to_vlmd(
                input_filepath=input_file,
                input_type=file_convert_function,
                data_dictionary_props=data_dictionary_props,
                include_all_fields=include_all_fields,
            )

            if output_type == "json":
                converted_dictionary = data_dictionaries["template_json"]
            else:
                converted_dictionary = data_dictionaries["template_csv"]["fields"]

        except ValidationError as err:
            logger.error(
                f"Error in validating and extracting dataset from {input_file}"
            )
            logger.error(err.message)
            raise ExtractionError(str(err.message))
        except Exception as err:
            logger.error(f"Error in extracting dictionary from dataset {input_file}")
            logger.error(err)
            raise ExtractionError(str(err))

        schema_type = "csv"
        schema = get_schema(converted_dictionary, schema_type=output_type)
        if output_type == "csv":
            schema = add_types_to_props(schema)
        if schema is None:
            message = f"Could not get schema for type = {schema_type}"
            logger.error(message)
            raise ValueError(message)
        try:
            logger.debug(f"Validating converted dictionary")
            jsonschema.validate(instance=converted_dictionary, schema=schema)
        except jsonschema.ValidationError as err:
            logger.error("Error in validating converted dictionary")
            raise err
        logger.debug("Converted dictionary is valid")

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
