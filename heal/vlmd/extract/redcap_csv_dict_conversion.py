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
from heal.vlmd.extract import utils
from heal.vlmd.extract.json_dict_conversion import convert_template_json
from heal.vlmd.mappings.redcap_field_mapping import type_mappings
from heal.vlmd.validate.utils import read_delim


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

    # TODO: FutureWarning: Downcasting behavior in `replace` is deprecated and will be removed in a future version.
    # To retain the old behavior, explicitly call `result.infer_objects(copy=False)`.
    # To opt-in to the future behavior, set `pd.set_option('future.no_silent_downcasting', True)`

    # downfill section (if blank -- given we read in with petl, blanks are "" but ffill takes in np.nan)
    source_dataframe["section"] = (
        source_dataframe.replace({"": np.nan}).groupby("form")["section"].ffill()
    )
    source_dataframe.fillna("", inplace=True)
    return source_dataframe.to_dict(orient="records")


def gather(source_fields: list[dict]) -> list[dict]:
    """
    maps and translates fields based on redcap field type
    to heal json
    """

    def __add_description(source_field, target_field):
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

    def __add_title(source_field, target_field):
        target_title = target_field.get("title", "")

        if target_title:
            return target_title
        elif source_field.get("label"):
            return target_title + utils.strip_html(source_field["label"].strip())
        else:
            return "No field label for this variable"

    def __add_section(source_field):
        if source_field.get("form"):
            return source_field["form"]

    def _add_metadata(source_field, target_field):
        target_field["description"] = __add_description(source_field, target_field)
        target_field["title"] = __add_title(source_field, target_field)
        target_field["section"] = __add_section(source_field)

    source_data_fields = [
        field for field in source_fields if field["type"] in list(type_mappings)
    ]

    target_fields = []
    for source_field in source_data_fields:
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

    return target_fields


def convert_redcapcsv(data_or_path, data_dictionary_props={}) -> dict[str, any]:
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

    # TODO: check if input if file_path or dataframe object
    if isinstance(data_or_path, (str, PathLike)):
        source_fields = read_from_file(data_or_path)
    elif not isinstance(data_or_path, pd.DataFrame):
        # TODO: log error
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
