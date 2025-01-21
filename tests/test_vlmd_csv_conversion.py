from io import StringIO

import pandas as pd
from pandas.testing import assert_frame_equal

from heal.vlmd.extract import utils
from heal.vlmd.extract.csv_dict_conversion import (
    _parse_string_objects,
    convert_datadict_csv,
)


def test_csv_conversion_valid_file(valid_csv_output, valid_converted_csv_to_json):
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    data_dictionary_props = {}

    result = convert_datadict_csv(
        input_file, data_dictionary_props=data_dictionary_props
    )
    assert list(result.keys()) == ["template_json", "template_csv"]
    assert list(result.get("template_json").keys()) == ["fields"]
    assert list(result.get("template_csv").keys()) == ["fields"]
    assert result.get("template_json") == valid_converted_csv_to_json
    assert result.get("template_csv") == valid_csv_output


def test_csv_conversion_valid_data(
    valid_array_data, valid_csv_output, valid_converted_csv_to_json
):
    data_dictionary_props = {}
    result = convert_datadict_csv(
        valid_array_data, data_dictionary_props=data_dictionary_props
    )
    assert list(result.keys()) == ["template_json", "template_csv"]
    assert list(result.get("template_json").keys()) == ["fields"]
    assert list(result.get("template_csv").keys()) == ["fields"]
    assert result.get("template_json") == valid_converted_csv_to_json
    assert result.get("template_csv") == valid_csv_output


def test_parse_string_objects(VALID_JSON_SCHEMA):
    field_properties = utils.flatten_properties(
        VALID_JSON_SCHEMA["properties"]["fields"]["items"]["properties"]
    )

    csv_data = """
        {
            "section": ["Enrollment", "Demographics"],
            "name": ["participant_id", "race"],
            "title": ["Participant Id", "Race"],
            "description": ["Unique identifier for participant", "Self-reported race"],
            "constraints.enum": ["", "1|2|3|4|5|6|7|8"],
            "constraints.pattern": ["[A-Z][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]", ""],
            "enumLabels": ["", "1=White|2=Black or African American|3=American Indian or Alaska Native|4=Native| 5=Hawaiian or Other Pacific Islander|6=Asian|7=Some other race|8=Multiracial|99=Not reported"],
            "custom.notes": ["This is a note", "This is a custom note"]
        }
    """
    csv_data_io = StringIO(csv_data)
    tbl_csv = pd.read_json(csv_data_io)

    expected_json_data = """
        {
            "section": ["Enrollment", "Demographics"],
            "name": ["participant_id", "race"],
            "title": ["Participant Id", "Race"],
            "description": ["Unique identifier for participant", "Self-reported race"],
            "constraints.enum": ["", ["1", "2", "3", "4", "5", "6", "7", "8"]],
            "constraints.pattern": ["[A-Z][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]", ""],
            "enumLabels": ["", {"1": "White", "2": "Black or African American", "3": "American Indian or Alaska Native", "4": "Native", "5": "Hawaiian or Other Pacific Islander", "6": "Asian", "7": "Some other race", "8": "Multiracial", "99": "Not reported"}],
            "custom.notes": ["This is a note", "This is a custom note"],
            "custom": [{"notes": "This is a note"}, {"notes": "This is a custom note"}]
        }
    """
    expected_json_data_io = StringIO(expected_json_data)
    expected_tbl_json = pd.read_json(expected_json_data_io)

    result = _parse_string_objects(tbl_csv, field_properties)
    assert_frame_equal(result, expected_tbl_json)
