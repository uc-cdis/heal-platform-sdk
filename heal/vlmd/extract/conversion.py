from functools import partial
from pathlib import Path

from cdislogging import get_logger

from heal.vlmd import mappings
from heal.vlmd.config import CSV_SCHEMA, JSON_SCHEMA, TOP_LEVEL_PROPS
from heal.vlmd.extract.csv_data_conversion import convert_dataset_csv
from heal.vlmd.extract.csv_dict_conversion import convert_datadict_csv
from heal.vlmd.extract.json_dict_conversion import convert_template_json
from heal.vlmd.extract.redcap_csv_dict_conversion import convert_redcap_csv
from heal.vlmd.extract.utils import sync_fields
from heal.vlmd.utils import clean_json_fields

logger = get_logger("vlmd-conversion", log_level="info")

choice_fxn = {
    "csv-data-set": convert_dataset_csv,
    "csv-data-dict": partial(
        convert_datadict_csv,
        rename_map=mappings.rename_map,
        recode_map=mappings.recode_map,
    ),
    "json-template": convert_template_json,
    "redcap-csv-dict": convert_redcap_csv,
}

ext_map = {
    ".csv": "csv-data-dict",
    ".json": "json-template",
}


def _detect_input_type(filepath, ext_to_input_type=ext_map):
    ext = filepath.suffix
    input_type = ext_to_input_type.get(ext, None)
    return input_type


def convert_to_vlmd(
    input_filepath,
    input_type: str = None,
    data_dictionary_props: dict = None,
    include_all_fields: bool = True,
) -> dict:
    """
    Converts a data dictionary or data file to HEAL compliant json or csv format.

    Args
        input_filepath (str): Path to input file. Currently converts data
            dictionaries in csv, json, and tsv.
        input_type (str): The input type. See keys of 'choice_fxn' dict for options, currently:
            csv-data-dict, csv-data-set, json-template, redcap-data-dict.
        data_dictionary_props (dict):
            The other data-dictionary level properties. By default,
            will give the data_dictionary `title` property as the file name stem.
        include_all_fields (bool): If true then csv dictionaries extracted from
            csv datasets will include columns for all fields in the schema.
            Useful for generating a template that can be manually updated.
            Default = True.
    Returns
        Dictionary with:
         1. csvtemplated array of fields.
         2. jsontemplated data dictionary object as specified by an originally drafted design doc.
            That is, a dictionary with title:<title>,description:<description>,data_dictionary:<fields>
            where data dictionary is an array of fields as specified by the JSON schema.

    """

    input_filepath = Path(input_filepath)

    input_type = input_type or _detect_input_type(input_filepath)
    logger.debug(f"Converting file '{input_filepath}' of input_type '{input_type}'")
    if input_type not in choice_fxn.keys():
        logger.error(f"Unexpected input type {input_type}")
        raise ValueError(
            f"Unexpected input_type '{input_type}', not in {choice_fxn.keys()}"
        )

    # get data dictionary package based on the input type
    data_dictionary_props = data_dictionary_props or {}
    data_dictionary_package = choice_fxn[input_type](
        input_filepath, data_dictionary_props
    )

    # For now we return the csv and json in one package.
    # If any multiple data dictionaries are needed then implement the methods in
    # https://github.com/HEAL/healdata-utils/blob/5080227454d8e731d46a51aa6933c93523eb3b9a/src/healdata_utils/conversion.py#L196
    package = data_dictionary_package

    # add schema version
    schema_version = {"schemaVersion": JSON_SCHEMA["version"]}
    for field in package["template_csv"]["fields"]:
        field.update({"schemaVersion": JSON_SCHEMA["version"], **field})

    if input_type == "csv-data-set":
        # add a value placeholder for description field
        description_placeholder = "description required"
        for field in package["template_json"]["fields"]:
            if not field.get("description"):
                field.update({"description": description_placeholder, **field})
        for field in package["template_csv"]["fields"]:
            if not field.get("description"):
                field.update({"description": description_placeholder, **field})

        if include_all_fields:
            # include schema fields that were not present in data file, don't include schema flags
            field_list = [
                key
                for key in CSV_SCHEMA["properties"].keys()
                if isinstance(CSV_SCHEMA["properties"][key], dict)
            ] + [
                key
                for key in CSV_SCHEMA["patternProperties"].keys()
                if isinstance(CSV_SCHEMA["patternProperties"][key], dict)
            ]
            package["template_csv"]["fields"] = sync_fields(
                package["template_csv"]["fields"], field_list
            )

    # remove empty json fields, add schema version (in TOP_LEVEL_PROPS)
    package["template_json"]["fields"] = clean_json_fields(
        package["template_json"]["fields"]
    )
    package["template_json"] = {**TOP_LEVEL_PROPS, **dict(package["template_json"])}

    return package
