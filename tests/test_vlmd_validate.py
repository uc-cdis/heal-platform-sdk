from unittest.mock import patch

import pytest
from jsonschema import SchemaError, ValidationError

from heal.vlmd import ExtractionError, vlmd_validate
from heal.vlmd.config import ALLOWED_OUTPUT_TYPES
from heal.vlmd.extract.csv_dict_conversion import RedcapExtractionError


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
    """vlmd_validate returns True for valid input"""
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    result = vlmd_validate(
        input_file, output_type=output_type, return_converted_output=False
    )
    assert result
    assert isinstance(result, bool)


@pytest.mark.parametrize("file_type", ["csv", "tsv", "json"])
def test_validate_with_json_output(
    file_type, valid_json_data, valid_converted_csv_to_json_output
):
    """vlmd_validate returns data when return_converted_output=True"""
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    result = vlmd_validate(input_file, output_type="json", return_converted_output=True)
    assert isinstance(result, dict)
    if file_type in ["csv", "tsv"]:
        assert result == valid_converted_csv_to_json_output
    if file_type == "json":
        assert result == valid_json_data


@pytest.mark.parametrize("file_type", ["csv", "json", "tsv"])
def test_invalid_missing_required_fields(file_type):
    """vlmd_validate raises Error for invalid input"""
    test_file = f"tests/test_data/vlmd/invalid/vlmd_missing_description.{file_type}"
    with pytest.raises(ValidationError) as e:
        vlmd_validate(input_file=test_file, schema_type="auto")
    expected_message = "'description' is a required property"
    assert expected_message in str(e.value)


def test_invalid_has_additional_properties():
    """vlmd_validate catches unallowed additional properties in json"""
    test_file = "tests/test_data/vlmd/invalid/vlmd_additional_properties.json"
    with pytest.raises(ValidationError) as e:
        vlmd_validate(input_file=test_file, schema_type="auto")
    expected_message = "Additional properties are not allowed"
    assert expected_message in str(e.value)


def test_invalid_redcap_dictionary():
    """vlmd_validate raises a Redcap error for invalid REDCap dictionary"""
    test_file = "tests/test_data/vlmd/invalid/vlmd_redcap_checkbox_unfilled.csv"
    with pytest.raises(RedcapExtractionError) as e:
        vlmd_validate(input_file=test_file, schema_type="auto")
    expected_message = "REDCap conversion error for mapping field 'aerobics'"
    assert expected_message in str(e.value)


@pytest.mark.parametrize(
    "file_type, expected_message, error_type",
    [
        ("json", "'foo' is not of type 'integer'", ValidationError),
        ("csv", "could not convert string to float: 'foo'", ExtractionError),
    ],
)
def test_invalid_incorrect_type(file_type, expected_message, error_type):
    """vlmd_validate raises error for incorrect types"""
    test_file = f"tests/test_data/vlmd/invalid/vlmd_string_in_maxLength.{file_type}"
    with pytest.raises(error_type) as e:
        vlmd_validate(input_file=test_file, schema_type="auto")
    assert expected_message in str(e.value)


def test_input_does_not_exist():
    """vlmd_validate raises error for non-existant input file"""
    file_dne = "does_not_exist.json"
    with pytest.raises(IOError) as e:
        vlmd_validate(input_file=file_dne, schema_type="auto")

    expected_message = f"Input file does not exist: {file_dne}"
    assert str(e.value) == expected_message


def test_unallowed_input_type(allowed_input_types):
    """vlmd_validate raises error for unallowed file type"""
    unallowed_file = "tests/test_data/vlmd/invalid/vlmd_invalid.txt"
    with pytest.raises(ValueError) as e:
        vlmd_validate(input_file=unallowed_file, schema_type="auto")

    expected_message = f"Input file must be one of {allowed_input_types}"
    assert str(e.value) == expected_message


def test_extract_unallowed_output():
    """vlmd_validate raises error for unallowed output type"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    unallowed_output = "txt"
    with pytest.raises(ValueError) as e:
        vlmd_validate(input_file, schema_type="json", output_type=unallowed_output)
    expected_message = f"Unrecognized output_type '{unallowed_output}' - should be in {ALLOWED_OUTPUT_TYPES}"
    assert expected_message in str(e.value)


@pytest.mark.parametrize("suffix", ["csv", "tsv"])
def test_validate_dataset_type(suffix):
    """vlmd_validate raises error when trying to validate data set"""
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid_data.{suffix}"
    dataset_file_type = f"dataset_{suffix}"
    with pytest.raises(ValueError) as e:
        vlmd_validate(input_file=test_file, file_type=dataset_file_type)

    expected_message = "Data set input file types are not valid dictionaries."
    assert str(e.value) == expected_message


@pytest.mark.parametrize("suffix", ["csv", "tsv"])
def test_validate_dataset_as_dictionary(suffix):
    """
    vlmd_validate raises ValidationError when trying to validate data set as a dictionary
    for json output
    """
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid_data.{suffix}"
    file_type = suffix
    with pytest.raises(ValidationError) as e:
        vlmd_validate(input_file=test_file, file_type=file_type, output_type="json")

    expected_message = "'description' is a required property"
    assert str(e.value.message) == expected_message


@pytest.mark.parametrize("suffix", ["csv", "tsv"])
def test_validate_dataset_as_dictionary_csv_output(suffix):
    """
    vlmd_validate raises Exception when trying to validate data set as a dictionary
    for csv output
    """
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid_data.{suffix}"
    file_type = suffix
    with pytest.raises(Exception) as e:
        vlmd_validate(input_file=test_file, file_type=file_type, output_type="csv")

    expected_message = "'description' is a required property in csv dictionaries"
    assert str(e.value) == expected_message


@pytest.mark.parametrize("test_schema_type", ["auto", "csv"])
def test_read_non_delim_data_in_csv(test_schema_type):
    test_file = "tests/test_data/vlmd/invalid/vlmd_text_data.csv"

    with pytest.raises(ValidationError) as e:
        vlmd_validate(test_file, test_schema_type)
    expected_message = "Could not read csv data from input"
    assert expected_message in str(e.value)


def test_incorrent_schema_type(allowed_schema_types):
    test_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
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
    """vlmd_extract raises ExtractionError when convert_to_vlmd raises Exception"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    fail_message = "Some conversion error"

    with patch("heal.vlmd.validate.validate.convert_to_vlmd") as mock_conversion:
        mock_conversion.side_effect = Exception(fail_message)
        with pytest.raises(ExtractionError) as e:
            vlmd_validate(input_file, output_type="json")
        assert fail_message in str(e.value)


def test_invalid_csv_schema(invalid_csv_schema):
    """vlmd_extract raises SchemaError for invalid CSV schema"""
    test_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"

    with patch("heal.vlmd.validate.validate.get_schema") as mock_get_schema:
        mock_get_schema.return_value = invalid_csv_schema
        with pytest.raises(SchemaError) as e:
            vlmd_validate(input_file=test_file, schema_type="csv")
        expected_message = "is not valid under any of the given schemas"
        assert expected_message in str(e.value)


def test_invalid_json_schema(invalid_json_schema):
    """vlmd_extract raises SchemaError for invalid JSON schema"""
    test_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    with patch("heal.vlmd.validate.validate.get_schema") as mock_get_schema:
        mock_get_schema.return_value = invalid_json_schema
        with pytest.raises(SchemaError) as e:
            vlmd_validate(input_file=test_file, schema_type="json")
        expected_message = "5 is not of type 'object'"
        assert expected_message in str(e.value)


def test_could_not_get_schema():
    """vlmd_validate raises ValueError if get_schema returns None"""
    schema_type = "json"
    test_file = f"tests/test_data/vlmd/valid/vlmd_valid.{schema_type}"

    with patch("heal.vlmd.validate.validate.get_schema") as mock_get_schema:
        mock_get_schema.return_value = None
        with pytest.raises(ValueError) as e:
            vlmd_validate(input_file=test_file, schema_type=schema_type)
        expected_message = f"Could not get schema for type = {schema_type}"
        assert expected_message in str(e.value)
