import os
from unittest.mock import patch
import pytest

from jsonschema import ValidationError
from heal.vlmd.config import ALLOWED_OUTPUT_TYPES, OUTPUT_FILE_PREFIX
from heal.vlmd.validate.validate_extract import ExtractionError, vlmd_validate_extract


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
def test_extract_valid_input(file_type, output_type, tmp_path):
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    expected_file_name = f"{tmp_path}/{OUTPUT_FILE_PREFIX}_vlmd_valid.{output_type}"

    result = vlmd_validate_extract(
        input_file, output_dir=tmp_path, output_type=output_type
    )
    assert result
    assert os.path.isfile(expected_file_name)
    # Maybe check that outfile has correct fields or actually compare with converted test data.


@pytest.mark.parametrize("file_type", ["csv", "json", "tsv"])
def test_valid_vlmd(file_type):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    result = vlmd_validate_extract(input_file=test_file, schema_type="auto")
    assert result == True
    result = vlmd_validate_extract(input_file=test_file, schema_type=file_type)
    assert result == True


@pytest.mark.parametrize("file_type", ["csv", "json", "tsv"])
def test_invalid_missing_required_fields(file_type):
    test_file = f"tests/test_data/vlmd/invalid/vlmd_missing_description.{file_type}"
    with pytest.raises(ValidationError) as e:
        vlmd_validate_extract(input_file=test_file, schema_type="auto")
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
        vlmd_validate_extract(input_file=test_file, schema_type="auto")
    assert expected_message in str(e.value)


def test_input_does_not_exist():
    file_dne = "does_not_exist.json"
    with pytest.raises(IOError) as e:
        vlmd_validate_extract(input_file=file_dne, schema_type="auto")

    expected_message = f"Input file does not exist: {file_dne}"
    assert str(e.value) == expected_message


def test_unallowed_input_type(allowed_input_types):
    unallowed_file = "vlmd_unallowed_type.txt"
    with pytest.raises(ValueError) as e:
        vlmd_validate_extract(input_file=unallowed_file, schema_type="auto")

    expected_message = f"Input file must be one of {allowed_input_types}"
    assert str(e.value) == expected_message


@pytest.mark.parametrize("test_schema_type", ["auto", "csv"])
def test_read_non_delim_data_in_csv(test_schema_type):
    test_file = "tests/test_data/vlmd/invalid/vlmd_text_data.csv"

    with pytest.raises(ValidationError) as e:
        vlmd_validate_extract(test_file, test_schema_type)
    expected_message = "Could not read csv data from input"
    assert expected_message in str(e.value)


def test_incorrent_schema_type(allowed_schema_types):
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.json"
    with pytest.raises(ValueError) as e:
        vlmd_validate_extract(input_file=test_file, schema_type="txt")

    expected_message = f"Schema type must be in {allowed_schema_types}"
    assert str(e.value) == expected_message


def test_invalid_converted_data():
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    fail_message = "Failed validation"

    with patch("jsonschema.validate") as mock_validate:
        mock_validate.side_effect = ValidationError(fail_message)
        with pytest.raises(ValidationError) as e:
            vlmd_validate_extract(input_file, output_type="json")
        assert fail_message in str(e.value)


def test_extract_unallowed_output():
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.json"
    unallowed_output = "txt"
    with pytest.raises(ValueError) as e:
        vlmd_validate_extract(
            input_file, schema_type="auto", output_type=unallowed_output
        )
    expected_message = f"Unrecognized output_type '{unallowed_output}' - should be in {ALLOWED_OUTPUT_TYPES}"
    assert expected_message in str(e.value)


def test_extract_failed_dict_write():
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.json"
    fail_message = "Error in writing converted dictionary"
    with patch("heal.vlmd.validate.validate_extract.write_vlmd_dict") as mock_write:
        mock_write.side_effect = Exception("some exception")
        with pytest.raises(ExtractionError) as e:
            vlmd_validate_extract(input_file, output_type="csv")
        assert fail_message in str(e.value)
