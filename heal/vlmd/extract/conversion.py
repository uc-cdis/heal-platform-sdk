from functools import partial
from pathlib import Path

from cdislogging import get_logger
from heal.vlmd.config import JSON_SCHEMA, TOP_LEVEL_PROPS
from heal.vlmd import mappings
from heal.vlmd.extract.csv_dict_conversion import convert_datadictcsv
from heal.vlmd.extract.json_dict_conversion import convert_templatejson
from heal.vlmd.utils import remove_empty_props


logger = get_logger("vlmd-conversion", log_level="debug")

choice_fxn = {
    "csv-data-dict": partial(
        convert_datadictcsv, renamemap=mappings.renamemap, recodemap=mappings.recodemap
    ),
    "json-template": convert_templatejson,
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
    input_type=None,
    data_dictionary_props=None,
):
    """
    Converts a data dictionary to HEAL compliant json or csv format.

    Args
        input_filepath (str): Path to input file. Currently converts data dictionaries in csv, json, and tsv.
        input_type (str): The input type. See keys of 'choice_fxn' dict for options, currently:
            csv-data-dict, json-template.
        data_dictionary_props (dict):
            The other data-dictionary level properties. By default, will give the data_dictionary `title` property as the file name stem.

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
    logger.debug(f"Data Dictionary Package keys {data_dictionary_package.keys()}")

    # For now we return the csv and json in one package.
    # If any multiple data dictionaries are needed then implement the methods in
    # https://github.com/HEAL/healdata-utils/blob/5080227454d8e731d46a51aa6933c93523eb3b9a/src/healdata_utils/conversion.py#L196
    package = data_dictionary_package

    # add schema version
    for field in package["templatecsv"]["fields"]:
        field.update({"schemaVersion": JSON_SCHEMA["version"], **field})

    # remove empty json fields add schema version (in TOP_LEVEL_PROPS)
    cleaned_fields = []
    for field in package["templatejson"]["fields"]:
        new_field = remove_empty_props(field)
        cleaned_fields.append(new_field)
    package["templatejson"]["fields"] = cleaned_fields

    package["templatejson"] = {**TOP_LEVEL_PROPS, **dict(package["templatejson"])}

    return package
