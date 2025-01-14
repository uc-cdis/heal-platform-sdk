import collections
import json
from os import PathLike
from pathlib import Path

import pandas as pd

from heal.vlmd.config import JSON_SCHEMA
from heal.vlmd.extract import utils


def convert_templatejson(
    json_template,
    data_dictionary_props: dict = None,
    fields_name: str = "fields",
) -> dict:
    """
    Converts a JSON file or dictionary conforming to HEAL specifications
    into a HEAL-specified data dictionary in both csv format and json format.

    Converts in-memory data or a path to a data dictionary file.

    If data_dictionary_props is specified, any properties passed in will be
    overwritten.

    Args
        json_template : str or path-like or an object that can be inferred as data by frictionless's Resource class.
            Data or path to data with the data being a tabular HEAL-specified data dictionary.
            This input can be any data object or path-like string excepted by a frictionless Resource object.
        data_dictionary_props : dict
            The HEAL-specified data dictionary properties.

    Returns
        A dictionary with two keys:
            - 'templatejson': the HEAL-specified JSON object.
            - 'templatecsv': the HEAL-specified tabular template.

    """

    if isinstance(json_template, (str, PathLike)):
        json_template_dict = json.loads(Path(json_template).read_text())
    elif isinstance(json_template, collections.abc.MutableMapping):
        json_template_dict = json_template
    else:
        raise ValueError(
            "json_template needs to be either dictionary-like or a path to a json"
        )

    if data_dictionary_props:
        for prop_name, prop in data_dictionary_props.items():
            # determine if you should write or overwrite the root level data dictionary props
            if not json_template_dict.get(prop_name):
                write_prop = True
            elif prop and prop != json_template_dict.get(prop_name):
                write_prop = True
            else:
                write_prop = False

            if write_prop:
                json_template_dict[prop_name] = prop

    fields_json = json_template_dict.pop(fields_name)
    data_dictionary_props = json_template_dict

    fields_schema = JSON_SCHEMA["properties"]["fields"]["items"]
    flattened_fields = pd.DataFrame(
        [utils.flatten_to_json_path(f, fields_schema) for f in fields_json]
    )
    flattened_data_dictionary_props = pd.Series(
        utils.flatten_to_json_path(data_dictionary_props, JSON_SCHEMA)
    )

    flattened_and_embedded = utils.embed_data_dictionary_props(
        flattened_fields, flattened_data_dictionary_props, JSON_SCHEMA
    )
    tbl_csv = (
        flattened_and_embedded.fillna("")
        .map(
            lambda v: utils.join_dict_items(v)
            if isinstance(v, collections.abc.MutableMapping)
            else v
        )
        .map(
            lambda v: utils.join_iter(v)
            if isinstance(v, collections.abc.MutableSequence)
            else v
        )
    )
    fields_csv = tbl_csv.to_dict(orient="records")

    template_json = {**data_dictionary_props, "fields": fields_json}
    template_csv = {**data_dictionary_props, "fields": fields_csv}

    return {"templatejson": template_json, "templatecsv": template_csv}
