from jsonschema import ValidationError
import pytest

from heal.vlmd.extract.conversion import convert_to_vlmd


def test_convert_valid_json_input(valid_json_output):
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    input_type = "json-template"
    result = convert_to_vlmd(input_file, input_type=input_type)

    assert list(result.keys()) == ["templatejson", "templatecsv"]
    assert list(result.get("templatejson").keys()) == [
        "schemaVersion",
        "title",
        "description",
        "fields",
    ]
    assert list(result.get("templatecsv").keys()) == ["title", "description", "fields"]
    assert result.get("templatejson") == valid_json_output


def test_convert_valid_csv_input(valid_json_output):
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    input_type = "csv-data-dict"
    result = convert_to_vlmd(input_file, input_type=input_type)

    assert list(result.keys()) == ["templatejson", "templatecsv"]
    assert list(result.get("templatejson").keys()) == [
        "schemaVersion",
        "title",
        "custom",
        "fields",
    ]
    assert list(result.get("templatecsv").keys()) == ["fields"]


def test_convert_unknown_input_type():
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    input_type = "txt"
    data_dictionary_props = {}
    with pytest.raises(ValueError) as e:
        convert_to_vlmd(
            input_file,
            input_type=input_type,
            data_dictionary_props=data_dictionary_props,
        )

    expected_message = f"Unexpected input_type '{input_type}'"
    assert expected_message in str(e.value)
