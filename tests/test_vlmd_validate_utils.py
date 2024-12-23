import json
from pathlib import Path

import pandas as pd
import pytest

from heal.vlmd.validate.utils import (
    detect_file_encoding,
    read_data_from_json_file,
    read_delim,
    get_schema,
)


def test_read_input_file():
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.json"
    result = read_data_from_json_file(test_file)
    assert isinstance(result, dict)
    assert "title" in result
    assert "description" in result
    assert "fields" in result


@pytest.mark.parametrize("file_type", ["csv", "json", "tsv"])
def test_detect_file_encoding(file_type):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    result = detect_file_encoding(test_file)
    assert result == "ascii"


@pytest.mark.parametrize("file_type", ["csv", "tsv"])
def test_read_delim(file_type):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"

    with open(test_file) as f:
        header_line = f.readline().strip("\n")
    file_suffix = Path(test_file).suffix.replace(".", "")
    if file_suffix == "csv":
        expected_data_columns = header_line.split(",")
    elif file_suffix == "tsv":
        expected_data_columns = header_line.split("\t")

    # get a pandas.dataFrame of the tabular data
    result = read_delim(test_file)
    assert result.columns.values.tolist() == expected_data_columns

    # dataFrame structure is column and values; this data matches the test input files
    expected_df = pd.DataFrame(
        {
            "section": {0: "Enrollment", 1: "Demographics"},
            "name": {0: "participant_id", 1: "race"},
            "title": {0: "Participant Id", 1: "Race"},
            "description": {
                0: "Unique identifier for participant",
                1: "Self-reported race",
            },
            "type": {0: "string", 1: "integer"},
            "format": {0: "", 1: ""},
            "constraints.maxLength": {0: "", 1: ""},
            "constraints.enum": {0: "", 1: "1|2|3|4|5|6|7|8"},
            "constraints.pattern": {
                0: "[A-Z][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
                1: "",
            },
            "constraints.maximum": {0: "", 1: ""},
            "constraints.minimum": {0: "", 1: ""},
            "enumLabels": {
                0: "",
                1: "1=White|2=Black or African American|3=American Indian or Alaska Native|4=Native| 5=Hawaiian or Other Pacific Islander|6=Asian|7=Some other race|8=Multiracial|99=Not reported",
            },
            "enumOrdered": {0: "", 1: ""},
            "missingValues": {0: "", 1: "99"},
            "trueValues": {0: "", 1: ""},
            "falseValues": {0: "", 1: ""},
            "custom.notes": {0: "This is a note", 1: "This is a custom note"},
        }
    )
    assert result.to_dict() == expected_df.to_dict()


def test_read_delim_unallowed_file_type():
    test_file = "test_data/vlmd/invalid/vlmd_invalid.txt"
    with pytest.raises(ValueError) as e:
        read_delim(test_file)

    expected_message = "Delimited file must be csv or tsv"
    assert expected_message in str(e.value)


@pytest.mark.parametrize("file_type", ["csv", "tsv"])
def test_get_schema_csv_file(file_type, VALID_CSV_SCHEMA):
    test_file = f"vlmd.{file_type}"
    expected_schema = {"type": "array", "items": VALID_CSV_SCHEMA}

    result = get_schema(test_file, "auto")
    assert result == expected_schema

    result = get_schema(test_file, file_type)
    assert result == expected_schema


@pytest.mark.parametrize("file_type", ["csv", "tsv"])
def test_get_schema_csv_list(file_type, VALID_CSV_SCHEMA, valid_array_data):
    expected_schema = {"type": "array", "items": VALID_CSV_SCHEMA}

    result = get_schema(valid_array_data, "auto")
    assert result == expected_schema

    result = get_schema(valid_array_data, file_type)
    assert result == expected_schema


@pytest.mark.parametrize("schema_type", ["auto", "json"])
def test_get_schema_json_file(schema_type, VALID_JSON_SCHEMA):
    test_file = "vlmd.json"

    result = get_schema(test_file, schema_type)
    assert result == VALID_JSON_SCHEMA


@pytest.mark.parametrize("schema_type", ["auto", "json"])
def test_get_schema_json_object(schema_type, VALID_JSON_SCHEMA):
    test_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    data = json.loads(Path(test_file).read_text())

    result = get_schema(data_or_path=data, schema_type=schema_type)
    assert result == VALID_JSON_SCHEMA


@pytest.mark.parametrize("invalid_data", [("set", "not", "a", "dict"), 5])
def test_get_schema_json_invalid_object(invalid_data, VALID_JSON_SCHEMA):
    with pytest.raises(ValueError) as e:
        get_schema(data_or_path=invalid_data, schema_type="json")
    expected_message = "Input should be path or dict"
    assert expected_message in str(e.value)


def test_get_schema_for_string_without_suffix():
    data = "Some string"
    result = get_schema(data_or_path=data, schema_type="auto")
    assert result == None


def test_get_schema_unknown_type(allowed_schema_types):
    test_file = "vlmd.json"
    unallowed_schema_type = "foo"
    assert unallowed_schema_type not in allowed_schema_types
    result = get_schema(test_file, unallowed_schema_type)
    assert result == None