from unittest.mock import patch
import pytest

from jsonschema import SchemaError, ValidationError
from heal.vlmd.config import ALLOWED_OUTPUT_TYPES, OUTPUT_FILE_PREFIX
from heal.vlmd import vlmd_validate, ExtractionError
from tests.conftest import invalid_json_schema


@pytest.mark.parametrize(
    "file_type, output_type",
    [
        ("csv", "csv"),
        ("csv", "json"),
        ("json", "csv"),
        ("json", "json"),
        ("tsv", "csv"),
        ("tsv", "json"),
    ],
)
def test_validate_valid_input(file_type, output_type):
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    result = vlmd_validate(
        input_file, output_type=output_type, return_converted_output=False
    )
    assert result


@pytest.mark.parametrize(
    "file_type, output_type",
    [
        ("csv", "json"),
        ("json", "json"),
        # ("tsv", "json"),
    ],
)
def test_validate_with_json_output(
    file_type, output_type, valid_json_output, valid_converted_csv_to_json_output
):
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    result = vlmd_validate(
        input_file, output_type=output_type, return_converted_output=True
    )
    assert isinstance(result, dict)
    if file_type == "csv":
        assert result == valid_converted_csv_to_json_output
    if file_type == "json":
        assert result == valid_json_output


@pytest.mark.parametrize("file_type", ["csv", "json", "tsv"])
def test_invalid_missing_required_fields(file_type):
    test_file = f"tests/test_data/vlmd/invalid/vlmd_missing_description.{file_type}"
    with pytest.raises(ValidationError) as e:
        vlmd_validate(input_file=test_file, schema_type="auto")
    expected_message = "'description' is a required property"
    assert expected_message in str(e.value)


@pytest.mark.parametrize(
    "file_type, expected_message, error_type",
    [
        ("json", "'foo' is not of type 'integer'", ValidationError),
        ("csv", "could not convert string to float: 'foo'", ExtractionError),
    ],
)
def test_invalid_incorrect_type(file_type, expected_message, error_type):
    test_file = f"tests/test_data/vlmd/invalid/vlmd_string_in_maxLength.{file_type}"
    with pytest.raises(error_type) as e:
        vlmd_validate(input_file=test_file, schema_type="auto")
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


@pytest.mark.parametrize("test_schema_type", ["auto", "csv"])
def test_read_non_delim_data_in_csv(test_schema_type):
    test_file = "tests/test_data/vlmd/invalid/vlmd_text_data.csv"

    with pytest.raises(ValidationError) as e:
        vlmd_validate(test_file, test_schema_type)
    expected_message = "Could not read csv data from input"
    assert expected_message in str(e.value)


def test_incorrent_schema_type(allowed_schema_types):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.json"
    with pytest.raises(ValueError) as e:
        vlmd_validate(input_file=test_file, schema_type="txt")

    expected_message = f"Schema type must be in {allowed_schema_types}"
    assert str(e.value) == expected_message


def test_invalid_converted_data():
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    fail_message = "Failed validation"

    with patch("jsonschema.validate") as mock_validate:
        mock_validate.side_effect = ValidationError(fail_message)
        with pytest.raises(ValidationError) as e:
            vlmd_validate(input_file, output_type="json")
        assert fail_message in str(e.value)


def test_extract_conversion_error():
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    fail_message = "Some conversion error"

    with patch("heal.vlmd.validate.validate.convert_to_vlmd") as mock_conversion:
        mock_conversion.side_effect = Exception(fail_message)
        with pytest.raises(ExtractionError) as e:
            vlmd_validate(input_file, output_type="json")
        assert fail_message in str(e.value)


def test_invalid_csv_schema(invalid_csv_schema):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.csv"

    with patch("heal.vlmd.validate.validate.get_schema") as mock_get_schema:
        mock_get_schema.return_value = invalid_csv_schema
        with pytest.raises(SchemaError) as e:
            vlmd_validate(input_file=test_file, schema_type="csv")
        expected_message = "is not valid under any of the given schemas"
        assert expected_message in str(e.value)


def test_invalid_json_schema(invalid_json_schema):
    test_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    with patch("heal.vlmd.validate.validate.get_schema") as mock_get_schema:
        mock_get_schema.return_value = invalid_json_schema
        with pytest.raises(SchemaError) as e:
            vlmd_validate(input_file=test_file, schema_type="json")
        expected_message = "5 is not of type 'object'"
        assert expected_message in str(e.value)


def test_could_not_get_schema():
    schema_type = "json"
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.{schema_type}"

    with patch("heal.vlmd.validate.validate.get_schema") as mock_get_schema:
        mock_get_schema.return_value = None
        with pytest.raises(ValueError) as e:
            vlmd_validate(input_file=test_file, schema_type=schema_type)
        expected_message = f"Could not get schema for type = {schema_type}"
        assert expected_message in str(e.value)
