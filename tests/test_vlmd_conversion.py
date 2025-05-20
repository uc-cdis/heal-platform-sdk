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


@pytest.mark.parametrize(
    "include_all_fields, expected_fields",
    [
        (False, ["name", "type", "constraints.enum", "schemaVersion", "description"]),
        (
            True,
            [
                "schemaVersion",
                "section",
                "name",
                "title",
                "description",
                "type",
                "format",
                "constraints.required",
                "constraints.maxLength",
                "constraints.enum",
                "constraints.pattern",
                "constraints.maximum",
                "constraints.minimum",
                "enumLabels",
                "enumOrdered",
                "missingValues",
                "trueValues",
                "falseValues",
                "custom",
                "standardsMappings[0].instrument.url",
                "standardsMappings[0].instrument.source",
                "standardsMappings[0].instrument.title",
                "standardsMappings[0].instrument.id",
                "standardsMappings[0].item.url",
                "standardsMappings[0].item.source",
                "standardsMappings[0].item.id",
                "relatedConcepts[0].url",
                "relatedConcepts[0].title",
                "relatedConcepts[0].source",
                "relatedConcepts[0].id",
            ],
        ),
    ],
)
def test_convert_dataset_csv_include_all_fields(include_all_fields, expected_fields):
    """Test the `include_all_fields` parameter"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid_data.csv"
    input_type = "csv-data-set"

    result = convert_to_vlmd(
        input_file, input_type=input_type, include_all_fields=include_all_fields
    )
    assert list(result.keys()) == ["template_json", "template_csv"]
    assert set(expected_fields) == set(list(result["template_csv"]["fields"][0].keys()))


def test_convert_dataset_csv_to_json(valid_converted_csv_dataset_to_json):
    """Test the conversion of a csv data set."""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid_data.csv"
    input_type = "csv-data-set"

    result = convert_to_vlmd(
        input_file,
        input_type=input_type,
    )
    assert list(result.keys()) == ["template_json", "template_csv"]
    assert result["template_json"] == valid_converted_csv_dataset_to_json


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
