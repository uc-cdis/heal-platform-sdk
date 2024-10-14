from unittest.mock import patch

from jsonschema import SchemaError, ValidationError
import pytest

from heal.vlmd.validate.json_validator import read_data_from_json_file
from heal.vlmd.validate.json_validator import vlmd_validate_json


@pytest.mark.parametrize("test_schema_type", ["auto", "json"])
def test_valid_json(test_schema_type):
    test_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    result = vlmd_validate_json(input_file=test_file, schema_type=test_schema_type)
    assert result == True


@pytest.mark.parametrize("test_schema_type", ["auto", "json"])
def test_invalid_json(test_schema_type):
    test_file = "tests/test_data/vlmd/invalid/vlmd_missing_description.json"

    with pytest.raises(ValidationError) as e:
        vlmd_validate_json(input_file=test_file, schema_type=test_schema_type)

    expected_message = f"'description' is a required property"
    assert expected_message in str(e.value)


def test_read_input_file():
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.json"
    result = read_data_from_json_file(test_file)
    assert isinstance(result, dict)
    assert "title" in result
    assert "description" in result
    assert "fields" in result


def test_invalid_json_schema(invalid_json_schema):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.json"

    with patch("heal.vlmd.validate.json_validator.get_schema") as mock_get_schema:
        mock_get_schema.return_value = invalid_json_schema
        with pytest.raises(SchemaError) as e:
            vlmd_validate_json(input_file=test_file, schema_type="json")
        expected_message = "5 is not of type 'object', 'boolean'"
        assert expected_message in str(e.value)
