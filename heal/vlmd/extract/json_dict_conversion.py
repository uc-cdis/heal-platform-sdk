import collections
import json
from os import PathLike
from pathlib import Path

import pandas as pd

from heal.vlmd.config import JSON_SCHEMA
from heal.vlmd.extract import utils


def convert_templatejson(
    jsontemplate,
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
        jsontemplate : str or path-like or an object that can be inferred as data by frictionless's Resource class.
            Data or path to data with the data being a tabular HEAL-specified data dictionary.
            This input can be any data object or path-like string excepted by a frictionless Resource object.
        data_dictionary_props : dict
            The HEAL-specified data dictionary properties.

    Returns
        A dictionary with two keys:
            - 'templatejson': the HEAL-specified JSON object.
            - 'templatecsv': the HEAL-specified tabular template.

    """

    if isinstance(jsontemplate, (str, PathLike)):
        jsontemplate_dict = json.loads(Path(jsontemplate).read_text())
    elif isinstance(jsontemplate, collections.abc.MutableMapping):
        jsontemplate_dict = jsontemplate
    else:
        raise ValueError(
            "jsontemplate needs to be either dictionary-like or a path to a json"
        )

    if data_dictionary_props:
        for propname, prop in data_dictionary_props.items():
            # determine if you should write or overwrite the root level data dictionary props
            if not jsontemplate_dict.get(propname):
                write_prop = True
            elif prop and prop != jsontemplate_dict.get(propname):
                write_prop = True
            else:
                write_prop = False

            if write_prop:
                jsontemplate_dict[propname] = prop

    fields_json = jsontemplate_dict.pop(fields_name)
    data_dictionary_props = jsontemplate_dict

    fields_schema = JSON_SCHEMA["properties"]["fields"]["items"]
    flattened_fields = pd.DataFrame(
        [utils.flatten_to_jsonpath(f, fields_schema) for f in fields_json]
    )
    flattened_data_dictionary_props = pd.Series(
        utils.flatten_to_jsonpath(data_dictionary_props, JSON_SCHEMA)
    )

    flattened_and_embedded = utils.embed_data_dictionary_props(
        flattened_fields, flattened_data_dictionary_props, JSON_SCHEMA
    )
    tbl_csv = (
        flattened_and_embedded.fillna("")
        .map(
            lambda v: utils.join_dictitems(v)
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
