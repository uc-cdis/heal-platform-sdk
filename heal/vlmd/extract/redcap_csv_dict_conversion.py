"""
Convert a REDCap data dictionary exported
in csv format to a heal-compliant json data dictionary.

STEPS
#1 fill section headers
#2 sort rows to allow proper row indexing
#3 make conditionals for each map function
"""

from os import PathLike

import numpy as np
import pandas as pd

import heal.vlmd.mappings.redcap_csv_headers as headers
from cdislogging import get_logger
from heal.vlmd.extract import utils
from heal.vlmd.extract.json_dict_conversion import convert_template_json
from heal.vlmd.mappings.redcap_field_mapping import type_mappings
from heal.vlmd.validate.utils import read_delim

logger = get_logger("redcap-conversion", log_level="debug")


def read_from_file(file_path):
    """
    Read csv from file.

    Returns dataframe.
    """
    source_dataframe = read_delim(file_path)
    return source_dataframe


def rename_and_fill(source_dataframe) -> list[dict]:
    """
    Rename columns to heal compliant, ffill

    Returns dict
    """
    source_dataframe = (
        source_dataframe.fillna("")
        .rename(columns=headers.mapping)
        .map(utils.strip_html)
    )

    # downfill section (if blank -- given we read in with petl, blanks are "" but ffill takes in np.nan)
    source_dataframe["section"] = (
        source_dataframe.replace({"": np.nan}).groupby("form")["section"].ffill()
    )
    # Recover any remaining np.nan (ie, not converted by 'ffill') back to "".
    # Include the 'infer_objects' method as described here
    # https://pandas.pydata.org/docs/whatsnew/v2.2.0.html#deprecated-automatic-downcasting
    source_dataframe = source_dataframe.fillna("").infer_objects(copy=False)
    return source_dataframe.to_dict(orient="records")


def _add_description(source_field: dict, target_field: dict) -> str:
    if source_field.get("label"):
        field_label = source_field["label"].strip()
    else:
        field_label = ""

    if source_field.get("section"):
        field_section = source_field["section"].strip() + ": "
    else:
        field_section = ""

    if target_field.get("description"):
        field_description = target_field["description"].strip()
    else:
        field_description = ""

    field_description = utils.strip_html(
        (field_section + field_label + field_description).strip()
    )
    if field_description:
        return field_description
    else:
        return "No field label for this variable"


def _add_title(source_field: dict, target_field: dict) -> str:
    target_title = target_field.get("title", "")

    if target_title:
        return target_title
    elif source_field.get("label"):
        return target_title + utils.strip_html(source_field["label"].strip())
    else:
        return "No field label for this variable"


def _add_section(source_field: dict):
    if source_field.get("form"):
        return source_field["form"]


def _add_metadata(source_field: dict, target_field: dict):
    target_field["description"] = _add_description(source_field, target_field)
    target_field["title"] = _add_title(source_field, target_field)
    target_field["section"] = _add_section(source_field)


def gather(source_fields: list[dict]) -> list[dict]:
    """Maps and translates fields from redcap to heal json"""

    source_data_fields = [
        field for field in source_fields if field["type"] in list(type_mappings)
    ]

    target_fields = []
    for source_field in source_data_fields:
        try:
            source_fieldtype = source_field["type"]
            target_field = type_mappings[source_fieldtype](source_field)
            # NOTE if one source_field generates more than 1 target field (ie checkbox) need to iterate through
            # if list (and hence not one to one mapping with source_field), assumes mandatory fields
            if isinstance(target_field, list):
                for _target_field in target_field:
                    assert "name" in _target_field and "type" in _target_field
                    _add_metadata(source_field, _target_field)
                    target_fields.append(_target_field)
            else:
                _add_metadata(source_field, target_field)
                target_field_with_name = {"name": source_field["name"]}
                target_field_with_name.update(target_field)
                target_fields.append(target_field_with_name)
        except Exception as err:
            logger.error(
                "REDCap conversion error for field '" f"{source_field['name']}" "'"
            )
            raise ValueError(str(err))

    return target_fields


def convert_redcap_csv(data_or_path, data_dictionary_props={}) -> dict[str, any]:
    """
    Takes in an exported Redcap Data Dictionary csv,
    and translates each field into a HEAL specified
    data dictionary based on field type (e.g., checkbox, radio, text and
    other conditional logic based on Redcap specifications.)


    > While there are a variety of options for Redcap exports (eg directly through
    the API or via an XML), the Redcap CSV provides an easy-to-edit format comfortable by
    technical and non-technical users.

    Parameters
    ----------
    data_or_path : str or path-like or a pandas DataFrame object.
        Data or path to data with the data being a tabular HEAL-specified data dictionary.
        This input can be any data object or path-like string excepted by a frictionless Resource object.
    data_dictionary_props : dict
        The HEAL-specified data dictionary properties.

    Returns
    -------
    dict
        A dictionary with two keys:
            - 'template_json': the HEAL-specified JSON object.
            - 'template_csv': the HEAL-specified tabular template.
    """

    if isinstance(data_or_path, (str, PathLike)):
        source_fields = read_from_file(data_or_path)
    elif not isinstance(data_or_path, pd.DataFrame):
        raise ValueError(
            "Input should be either dataframe or path to REDCap dictionary csv export"
        )
    else:
        source_fields = data_or_path
    source_fields = rename_and_fill(source_fields)
    target_fields = gather(source_fields)

    data_dictionary = data_dictionary_props.copy()
    data_dictionary["fields"] = target_fields

    package = convert_template_json(data_dictionary)
    return package
