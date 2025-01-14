from os import PathLike
from pathlib import Path
import re

import pandas as pd

from heal.vlmd.config import JSON_SCHEMA
from heal.vlmd.extract import utils
from heal.vlmd.validate.utils import read_delim


def convert_datadict_csv(
    csv_template: str,
    data_dictionary_props: dict,
    rename_map: dict = None,
    recode_map: dict = None,
    drop_list: dict = None,
    item_sep: str = "|",
    key_val_sep: str = "=",
) -> dict:
    """
    Converts a CSV conforming to HEAL specifications (but see 2 additional notes below)
    into a HEAL-specified data dictionary in both csv format and json format.

    Converts an in-memory data dictionary or a path to a data dictionary file into a HEAL-specified tabular template by:
        1. Adding missing fields, and
        2. Converting fields from a specified mapping.
            NOTE: currently this mapping is only float/num to number or text/char to string (case insensitive)
                In future versions, there will be a specified module for csv input mappings.

    Args

        csv_template : str or path-like or an object that can be inferred as data by frictionless's Resource class.
            Data or path to data with the data being a tabular HEAL-specified data dictionary.
            This input can be any data object or path-like string excepted by a frictionless Resource object.
        data_dictionary_props : dict
            The HEAL-specified data dictionary properties.
        rename_map: A mapping of source (current) column headers to target (desired -- conforming to CVS HEAL spec)
            column headers
        recode_map: A mapping of values for each column in HEAL spec -- {..."column_name":{"old_value":"new_value"...}...}
        drop_list: a list of variables to drop from headers before processing
        item_sep:str (default:"|") Used to split stringified items (in objects and arrays)
        key_val_sep:str (default:"=") Used to split stringified each key-value pair

    Returns
        A dictionary with two keys:
            - 'templatejson': the HEAL-specified JSON object.
            - 'templatecsv': the HEAL-specified tabular template.

    """

    # get transforms
    # cast numbers explicitly based on schema
    # this is needed in case there is only one record in a string column that is a number (ie don't want to convert)
    def infer_delim(series: pd.Series, char_list: list, firstmatch: bool):
        """infer the delimiter by the highest frequency by row higest occuring character
        can either take only the first match or all matches for each row"""
        combined_pattern = "|".join(map(re.escape, char_list))

        try:
            # get most frequent delimiter per row
            most_freq_chars = (
                series.rename_axis("row")
                .str.extractall(f"({combined_pattern})")
                .squeeze(
                    "rows"
                )  # only 1 row, dont want to squeeze to scalar so spec rows
                .pipe(
                    lambda s: s.unstack("match")[0] if firstmatch else s
                )  # if first match specified
                .groupby("row")
                .value_counts()
                .unstack()
                .idxmax(axis=1)
            )
        except KeyError:
            return None

        try:
            # infer delim by character with most per row max frequencies
            inferred_delim = most_freq_chars.value_counts().sort_values().index[-1]
        except IndexError:
            return None

        return inferred_delim

    if isinstance(csv_template, (str, PathLike)):
        template_tbl = read_delim(str(Path(csv_template)))
    else:
        template_tbl = pd.DataFrame(csv_template)

    if not rename_map:
        rename_map = {}

    if not recode_map:
        recode_map = {}

    if not drop_list:
        drop_list = []

    slugify = lambda s: s.strip().lower().replace("_", "-").replace(" ", "-")
    # flattened properties
    field_properties = utils.flatten_properties(
        JSON_SCHEMA["properties"]["fields"]["items"]["properties"]
    )

    # init to-be formatted tables
    tbl_csv = template_tbl.copy()
    # transform each column with slugified mappings, harmonizing delims (if array, object)
    for column_name in tbl_csv.columns.tolist():
        slugified_col = slugify(column_name)
        new_column_name = column_name

        # rename based on slugified names or original col names
        new_column_name = rename_map.get(slugified_col) or rename_map.get(column_name)
        if new_column_name:
            tbl_csv.rename(columns={column_name: new_column_name}, inplace=True)
        else:
            new_column_name = column_name

        # recode slugified old names to accepted names
        if new_column_name in recode_map.keys():
            tbl_csv[new_column_name] = (
                tbl_csv[new_column_name]
                .apply(slugify)
                .replace(recode_map[new_column_name])
            )

        if new_column_name in drop_list:
            del tbl_csv[new_column_name]

        # NOTE: the below methodology uses the schema to instruct how to convert to json.
        field_prop_name = utils.find_prop_name(new_column_name, field_properties)
        field_prop = field_properties.get(field_prop_name)
        # infer delimiters of stringified lists (note: stringified lists are identified from schema)

        if field_prop_name:
            if field_prop["type"] == "integer":
                tbl_csv[new_column_name] = tbl_csv[new_column_name].apply(
                    lambda s: int(float(s)) if s else s
                )
            elif field_prop["type"] == "number":
                tbl_csv[new_column_name] = tbl_csv[new_column_name].astype(float)
            elif field_prop["type"] == "object":
                possible_key_val = ["=", ":"]
                possible_list = [";", "|"]
                key_val_sep = (
                    infer_delim(
                        tbl_csv[new_column_name], possible_key_val, firstmatch=True
                    )
                    or "="
                )
                item_sep = (
                    infer_delim(
                        tbl_csv[new_column_name], possible_list, firstmatch=False
                    )
                    or "|"
                )

                tbl_csv[new_column_name] = (
                    tbl_csv[new_column_name]
                    .str.replace(key_val_sep, "=")
                    .str.replace(item_sep, "|")
                )

            elif field_prop["type"] == "array":
                possible_list = [";", "|"]
                item_sep = (
                    infer_delim(
                        tbl_csv[new_column_name], possible_list, firstmatch=False
                    )
                    or "|"
                )
                tbl_csv[new_column_name] = tbl_csv[new_column_name].replace(
                    item_sep, "|"
                )

    # parse string objects and array to create the dict (json) instance
    tbl_json = tbl_csv.copy()
    for column_name in tbl_json.columns.tolist():
        # NOTE: the below methodology uses the schema to instruct how to convert to json.
        field_prop_name = utils.find_prop_name(column_name, field_properties)
        field_prop = field_properties.get(field_prop_name)
        if field_prop:
            if field_prop["type"] == "object":
                tbl_json[column_name] = tbl_csv[column_name].apply(
                    utils.parse_dictionary_str, item_sep="|", key_val_sep="="
                )

            elif field_prop["type"] == "array":
                tbl_json[column_name] = tbl_csv[column_name].apply(
                    utils.parse_list_str, item_sep="|"
                )
        # columns not included in schema (custom or other)
        else:
            if column_name.split(".")[0] == "custom":
                if not "custom" in tbl_json:
                    tbl_json["custom"] = [{}] * len(tbl_json)

                for i in range(len(tbl_csv)):
                    value = tbl_csv[column_name].iloc[i]
                    if value:
                        custom = {}
                        parts = column_name.split(".")[1:]

                        for key in reversed(parts):
                            result = {key: value}

                        tbl_json["custom"].iloc[i].update(result)
            else:
                tbl_json[column_name] = tbl_csv[column_name]

    # drop all custom columns (as I have nested already)
    tbl_json.drop(columns=tbl_json.filter(regex="^custom\\.").columns, inplace=True)

    # refactor (i.e., cascade, move up to root) properties if present in all records
    refactored_props, tbl_json = utils.refactor_field_props(
        tbl_json, schema=JSON_SCHEMA
    )

    # data dictionary root level properties
    data_dictionary_props_csv = dict(data_dictionary_props)
    data_dictionary_props_json = {
        **data_dictionary_props,
        **utils.unflatten_from_json_path(refactored_props.to_dict()),
    }

    # create the data dictionary objects
    fields_json = [
        utils.unflatten_from_json_path(record)
        for record in tbl_json.to_dict(orient="records")
    ]
    template_json = dict(**data_dictionary_props_json, fields=fields_json)

    fields_csv = tbl_csv.to_dict(orient="records")
    template_csv = dict(**data_dictionary_props_csv, fields=fields_csv)

    return {"templatejson": template_json, "templatecsv": template_csv}
