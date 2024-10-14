import charset_normalizer
import jsonschema
import pandas as pd
from pathlib import Path

from cdislogging import get_logger
from heal.vlmd.config import CSV_SCHEMA, JSON_SCHEMA

logger = get_logger("VLMD_UTILS", log_level="debug")


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


def read_delim(file_path, castdtype="string"):
    """
    reads in a tabular file (ie spreadsheet) after detecting
    encoding and file extension without any type casting.

    currently supports csv and tsv

    defaults to not casting values (ie all columns are string dtypes)
    and not parsing strings into NA values (eg "" is kept as "")
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
        file_path, sep=sep, encoding=encoding, dtype=castdtype, keep_default_na=False
    )

    return file_encoding


def get_schema(input_file: str, schema_type: str):
    """
    Get the schema for the specified schema_type.
    Use the input_file suffix for "auto".

    Args:
        input_file (str): the path of the input VLMD file to be validated
        schema_type (str): the type of the schema that can be validated against.
            Allowed values for now are “csv”, “tsv”, “json” and “auto”. Defaults to “auto”
    Returns:
        schema
    """

    file_suffix = Path(input_file).suffix.replace(".", "")
    if schema_type == "csv" or (schema_type == "auto" and file_suffix == "csv"):
        schema = {"type": "array", "items": CSV_SCHEMA}
        logger.debug("Validator will use CSV schema")
        return schema
    elif schema_type == "tsv" or (schema_type == "auto" and file_suffix == "tsv"):
        schema = {"type": "array", "items": CSV_SCHEMA}
        logger.debug("Validator will use CSV schema for TSV file")
        return schema
    elif schema_type == "json" or (schema_type == "auto" and file_suffix == "json"):
        schema = JSON_SCHEMA
        logger.debug("Validator will use json schema")
        return schema
    else:
        return None


def add_missing_type(propname: str, prop, schema: dict):
    """
    Add types to properties.

    Args:
        propname (str): property name
        prop (str or dict): property
        schema (dict): schema

    Returns:
        schema

    """
    missing_values = ["", None]  # NOTE: include physical rep and logical for now
    if propname in schema.get("required", []):
        # if required value: MUST be NOT missing value and the property
        newprop = {"allOf": [prop, {"not": {"enum": missing_values}}]}
    else:
        # if not required value: MUST be property OR the specified missing value
        newprop = {"anyOf": [prop, {"enum": missing_values}]}
    return newprop


def add_types_to_props(schema: dict) -> dict:
    """
    Add missing types to the schema for validating csv style data.

    Args:
        schema

    Returns:
        schema
    """

    props_with_missing = {}
    for propname, prop in schema.get("items", {}).get("properties", {}).items():
        props_with_missing[propname] = add_missing_type(propname, prop, schema)

    patterns_with_missing = {}
    for patternname, prop in (
        schema.get("items", {}).get("patternProperties", {}).items()
    ):
        patterns_with_missing[patternname] = add_missing_type(patternname, prop, schema)

    schema = {"type": "array", "items": {}}
    schema["items"]["properties"] = props_with_missing
    schema["items"]["patternProperties"] = patterns_with_missing

    return schema
