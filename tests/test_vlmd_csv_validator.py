from unittest.mock import patch
from jsonschema import SchemaError, ValidationError
import pytest

from heal.vlmd.validate.csv_validator import vlmd_validate_csv


@pytest.mark.parametrize("test_schema_type", ["auto", "csv"])
def test_valid_csv(test_schema_type):
    test_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"

    result = vlmd_validate_csv(test_file, test_schema_type)
    assert result == True


@pytest.mark.parametrize("test_schema_type", ["auto", "csv"])
def test_invalid_csv(test_schema_type):
    test_file = "tests/test_data/vlmd/invalid/vlmd_string_in_maxLength.csv"

    with pytest.raises(ValidationError) as e:
        vlmd_validate_csv(test_file, test_schema_type)
    expected_message = "'foo' is not valid under any of the given schemas"
    assert expected_message in str(e.value)


@pytest.mark.parametrize("test_schema_type", ["auto", "csv"])
def test_read_non_delim_data_in_csv(test_schema_type):
    test_file = "tests/test_data/vlmd/invalid/vlmd_text_data.csv"

    with pytest.raises(ValueError) as e:
        vlmd_validate_csv(test_file, test_schema_type)
    expected_message = "Could not read data from file"
    assert expected_message in str(e.value)


def test_unallowed_schema_type(allowed_schema_types):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.csv"
    with pytest.raises(ValueError) as e:
        vlmd_validate_csv(input_file=test_file, schema_type="txt")
    expected_message = f"Schema type must be in {allowed_schema_types}"
    assert expected_message in str(e.value)


def test_invalid_csv_schema(invalid_csv_schema):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.csv"

    with patch("heal.vlmd.validate.csv_validator.get_schema") as mock_get_schema:
        mock_get_schema.return_value = invalid_csv_schema
        with pytest.raises(SchemaError) as e:
            vlmd_validate_csv(input_file=test_file, schema_type="csv")
        expected_message = "is not valid under any of the given schemas"
        print(f"Got message {str(e.value)}")
        assert expected_message in str(e.value)
