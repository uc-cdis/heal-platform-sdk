from unittest.mock import patch
import pytest

from jsonschema import ValidationError
from heal.vlmd import vlmd_validate


@pytest.mark.parametrize("file_type", ["csv", "json", "tsv"])
def test_valid_vlmd(file_type):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    result = vlmd_validate(input_file=test_file, schema_type="auto")
    assert result == True
    result = vlmd_validate(input_file=test_file, schema_type=file_type)
    assert result == True


def test_invalid_vlmd_csv():
    pass


def test_invalid_vlmd_tsv():
    pass


def test_invalid_vlmd_json():
    test_file = "tests/test_data/vlmd/invalid/vlmd_missing_description.json"
    with pytest.raises(ValidationError) as e:
        vlmd_validate(input_file=test_file, schema_type="auto")

    expected_message = f"'description' is a required property"
    assert expected_message in str(e.value)


def test_input_does_not_exist():
    file_dne = "does_not_exist.json"
    with pytest.raises(IOError) as e:
        vlmd_validate(input_file=file_dne, schema_type="auto")

    expected_message = f"Input file does not exist: {file_dne}"
    assert str(e.value) == expected_message


def test_unallowed_input_type(allowed_input_types):
    unallowed_file = "vlmd_unallowed_type.txt"
    with pytest.raises(ValueError) as e:
        vlmd_validate(input_file=unallowed_file, schema_type="auto")

    expected_message = f"Input file must be one of {allowed_input_types}"
    assert str(e.value) == expected_message


def test_incorrent_schema_type(allowed_schema_types):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.json"
    with pytest.raises(ValueError) as e:
        vlmd_validate(input_file=test_file, schema_type="txt")

    expected_message = f"Schema type must be in {allowed_schema_types}"
    assert str(e.value) == expected_message
