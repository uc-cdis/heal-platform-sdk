import csv
import json
import os
from pathlib import Path

import pandas as pd
from cdislogging import get_logger

from heal.vlmd.config import OUTPUT_FILE_PREFIX

logger = get_logger("vlmd-file-utils", log_level="debug")


# file writing
def get_output_filepath(output_dir, infile_name, output_type="auto"):
    """
    Generate the output file path.
    Replace path to infile_name with output_dir.
    Replace suffix with 'json' if needed.

    Args:
      output_dir: output directory
      infile_name: the input file that dictionary is extracted from.
      output_type (str): the type of file to write to, currently csv and json.
        The default is "auto" which gets the type from the suffix of the input file name.

    Returns:
      string with output filepath:
          <output_dir>/<prefix>_<infile_name>.<suffix>
    """

    prefix = OUTPUT_FILE_PREFIX
    file_name = os.path.basename(infile_name)
    if output_type == "auto":
        output_filepath = f"{output_dir}/{prefix}_{file_name}"
    else:
        file_name = os.path.splitext(file_name)[0]
        output_filepath = f"{output_dir}/{prefix}_{file_name}.{output_type}"
    return output_filepath


def write_vlmd_dict(dictionary, output_filepath, file_type="auto"):
    """
    Write the json format dictionary to file.

    Args:
      dictionary (dict or array): data to write to file
      output_dir (path): path for output file
      file_type (str): type of file to write - "auto", "csv", "json".
          "auto" will get the type from the output_filepath suffix.
          The default is "auto".
    Returns:
      True for successful write of csv or json.
      None for unrecognized output type.
    """
    if not output_filepath:
        logger.error("Empty output_filepath in write_vlmd_dict")
        raise ValueError("Empty output_filepath in write_vlmd_dict")

    output_filepath = Path(output_filepath)

    if file_type == "auto":
        file_type = output_filepath.suffix.replace(".", "")

    logger.debug(f"Output dictionary type is {file_type}")
    dirname = os.path.dirname(output_filepath)
    if dirname != "":
        os.makedirs(dirname, exist_ok=True)

    if file_type == "json":
        if not isinstance(dictionary, dict):
            msg = "Json output type should have dict data"
            logger.error(msg)
            raise ValueError(msg)
        with open(output_filepath, "w") as f:
            json.dump(dictionary, f, indent=4)
        return True

    if file_type == "csv":
        if not isinstance(dictionary, list):
            msg = "CSV output type should have list data"
            logger.error(msg)
            raise ValueError(msg)
        quoting = csv.QUOTE_MINIMAL
        pd.DataFrame(dictionary).to_csv(output_filepath, quoting=quoting, index=False)
        return True

    logger.warning(f"Unknown file type {file_type}")
    return None
