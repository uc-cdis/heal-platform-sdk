import json
import os
from pathlib import Path
from typing import Dict

import charset_normalizer
import pandas as pd
from cdislogging import get_logger

from heal.vlmd.config import CSV_SCHEMA, JSON_SCHEMA

logger = get_logger("validate-utils", log_level="debug")


def detect_file_encoding(file_path):
    """
    detects file encoding using charset_normalizer package
    """

    with open(file_path, "rb") as f:
        data = f.read()
        encoding_for_input = charset_normalizer.detect(data)

    is_confident = encoding_for_input["confidence"] == 1
    if not is_confident:
        logger.warning("Be careful, the detected file encoding for:")
        logger.warning(f"{file_path}")
        logger.warning(r"has less than 100% confidence")

    return encoding_for_input["encoding"]


def read_delim(file_path, cast_d_type="string"):
    """
    reads in a tabular file (ie spreadsheet) after detecting
    encoding and file extension without any type casting.

    currently supports csv and tsv

    defaults to not casting values (ie all columns are string dtypes)
    and not parsing strings into NA values (eg "" is kept as "")

    Returns a pandas dataframe
    """
    ext = Path(file_path).suffix
    if ext == ".csv":
        sep = ","
    elif ext == ".tsv":
        sep = "\t"
    else:
        raise ValueError("Delimited file must be csv or tsv")

    encoding = detect_file_encoding(file_path)
    file_encoding = pd.read_csv(
        file_path, sep=sep, encoding=encoding, dtype=cast_d_type, keep_default_na=False
    )

    return file_encoding


def read_data_from_json_file(input_file: str) -> Dict:
    """Loads the data from a json input file"""
    data = json.loads(Path(input_file).read_text())
    return data


def get_schema(data_or_path, schema_type: str):
    """
    Get the schema for the specified schema_type.
    Use the input_file suffix for "auto".

    Args:
        data_or_path: json dictionary or path to input file
        schema_type (str): the type of the schema that can be validated against.
            Allowed values for now are “csv”, “tsv”, “json” and “auto”. Defaults to “auto”
    Returns:
        schema (dict)
    """

    if isinstance(data_or_path, (str, os.PathLike)):
        dictionary_type = Path(data_or_path).suffix.replace(".", "")
    elif isinstance(data_or_path, dict):
        dictionary_type = "json"
    elif isinstance(data_or_path, list):
        dictionary_type = "csv"
    else:
        logger.error("Cannot get schema. Input is not path or dict or list")
        raise ValueError("Input should be path or dict or list")

    if schema_type == "csv" or (schema_type == "auto" and dictionary_type == "csv"):
        schema = {"type": "array", "items": CSV_SCHEMA}
        logger.debug("Validator will use CSV schema")
        return schema
    if schema_type == "tsv" or (schema_type == "auto" and dictionary_type == "tsv"):
        schema = {"type": "array", "items": CSV_SCHEMA}
        logger.debug("Validator will use CSV schema for TSV file")
        return schema
    if schema_type == "json" or (schema_type == "auto" and dictionary_type == "json"):
        schema = JSON_SCHEMA
        logger.debug("Validator will use json schema")
        return schema

    return None
