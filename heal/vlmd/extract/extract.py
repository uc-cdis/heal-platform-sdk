from os.path import isfile
from pathlib import Path

from cdislogging import get_logger

from heal.vlmd import ExtractionError, vlmd_validate
from heal.vlmd.config import (
    ALLOWED_FILE_TYPES,
    ALLOWED_INPUT_TYPES,
    ALLOWED_OUTPUT_TYPES,
)
from heal.vlmd.file_utils import get_output_filepath, write_vlmd_dict

logger = get_logger("extract", log_level="debug")


def vlmd_extract(
    input_file, file_type="auto", output_dir=".", output_type="json"
) -> bool:
    """
    Extract a HEAL compliant csv and json format VLMD data dictionary
    from the input file.

    Args:
        input_file (str): the path of the input HEAL VLMD file to be extracted
            into HEAL-compliant VLMD file(s).
        file_type (str): the type of the input file that will be extracted into a
            HEAL-compliant VLMD file.
            Allowed values are "auto", “csv”, "json", "tsv".
            Defaults to “auto”.
        output_dir (str): the directory of where the extracted VLMD file will
            be written. Defaults to “.”
        output_type (str): format of dictionary to write: "csv" or "json".
            The default is "json".

    Returns:
        True if the input is valid and is successfully converted and written.
        Raises ExtractionError in input VLMD is not valid or could not be converted.
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

    if output_type not in ALLOWED_OUTPUT_TYPES:
        raise ExtractionError(
            f"Unrecognized output_type '{output_type}' - should be in {ALLOWED_OUTPUT_TYPES}"
        )

    # validate
    try:
        converted_dictionary = vlmd_validate(
            input_file, output_type=output_type, return_converted_output=True
        )
    except Exception as e:
        logger.error(f"Error in validating and extracting dictionary from {input_file}")
        logger.error(e)
        raise ExtractionError(str(e))

    # write to file
    output_filepath = get_output_filepath(
        output_dir, input_file, output_type=output_type
    )
    logger.info(f"Writing converted dictionary to {output_filepath}")
    try:
        write_vlmd_dict(converted_dictionary, output_filepath, file_type=output_type)
    except Exception as e:
        logger.error("Error in writing converted dictionary")
        logger.error(e)
        raise ExtractionError("Error in writing converted dictionary")

    return True
