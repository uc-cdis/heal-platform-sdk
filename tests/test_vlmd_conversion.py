from jsonschema import ValidationError
import pytest

from heal.vlmd.extract.conversion import convert_to_vlmd


def test_convert_valid_json_input(valid_json_output):
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    input_type = "json-template"
    result = convert_to_vlmd(input_file, input_type=input_type)

    assert list(result.keys()) == ["template_json", "template_csv"]
    assert list(result.get("template_json").keys()) == [
        "schemaVersion",
        "title",
        "description",
        "fields",
    ]
    assert list(result.get("template_csv").keys()) == ["title", "description", "fields"]
    assert result.get("template_json") == valid_json_output


@pytest.mark.parametrize(
    "input_file, expected_json_keys",
    [
        (
            "tests/test_data/vlmd/valid/vlmd_valid.csv",
            [
                "schemaVersion",
                "title",
                "fields",
            ],
        ),
        (
            "tests/test_data/vlmd/valid/vlmd_test_custom_root_level.csv",
            [
                "schemaVersion",
                "title",
                "custom",
                "fields",
            ],
        ),
    ],
)
def test_convert_valid_csv_input(input_file, expected_json_keys):
    input_type = "csv-data-dict"
    result = convert_to_vlmd(input_file, input_type=input_type)

    assert list(result.keys()) == ["template_json", "template_csv"]
    assert list(result.get("template_json").keys()) == expected_json_keys
    assert list(result.get("template_csv").keys()) == ["fields"]


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
