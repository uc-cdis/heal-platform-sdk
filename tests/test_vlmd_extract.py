import json
import os
from unittest.mock import patch

import pytest

from heal.vlmd.config import ALLOWED_OUTPUT_TYPES, OUTPUT_FILE_PREFIX
from heal.vlmd.extract.extract import ExtractionError, vlmd_extract

test_title = "Test title for unit tests"


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

    result = vlmd_extract(
        input_file, test_title, output_dir=tmp_path, output_type=output_type
    )
    assert result
    assert os.path.isfile(expected_file_name)
    if output_type == "json":
        with open(expected_file_name, "r") as f:
            data = json.load(f)
        assert "fields" in data.keys()
        assert "schemaVersion" in data.keys()


@pytest.mark.parametrize(
    "input_file, expected_message, error_type",
    [
        (
            "tests/test_data/vlmd/invalid/vlmd_string_in_maxLength.csv",
            "could not convert string to float: 'foo'",
            ExtractionError,
        ),
        (
            "tests/test_data/vlmd/invalid/vlmd_missing_description.csv",
            "'description' is a required property",
            ExtractionError,
        ),
        (
            "tests/test_data/vlmd/invalid/vlmd_missing_name.csv",
            "'name' is a required property",
            ExtractionError,
        ),
    ],
)
def test_extract_invalid_input(input_file, expected_message, error_type):
    with pytest.raises(error_type) as e:
        vlmd_extract(input_file, test_title)
    assert expected_message in str(e.value)


def test_extract_unallowed_input_type():
    input_file = "tests/test_data/vlmd/invalid/vlmd_invalid.txt"
    with pytest.raises(ExtractionError) as e:
        vlmd_extract(input_file, test_title)
    expected_message = "Input file must be one of"
    assert expected_message in str(e.value)


def test_extract_unallowed_file_type():
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    with pytest.raises(ExtractionError) as e:
        vlmd_extract(input_file, test_title, file_type="txt")
    expected_message = "File type must be one of"
    assert expected_message in str(e.value)


def test_extract_input_does_not_exist(tmp_path):
    input_file = f"{tmp_path}/foo.csv"
    with pytest.raises(ExtractionError) as e:
        vlmd_extract(input_file, test_title)
    expected_message = f"Input file does not exist: {input_file}"
    assert expected_message in str(e.value)


def test_extract_unallowed_output():
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    unallowed_output = "txt"
    with pytest.raises(ExtractionError) as e:
        vlmd_extract(
            input_file, test_title, file_type="json", output_type=unallowed_output
        )
    expected_message = f"Unrecognized output_type '{unallowed_output}' - should be in {ALLOWED_OUTPUT_TYPES}"
    assert expected_message in str(e.value)


def test_extract_failed_dict_write():
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    fail_message = "Error in writing converted dictionary"
    with patch("heal.vlmd.extract.extract.write_vlmd_dict") as mock_write:
        mock_write.side_effect = Exception("some exception")
        with pytest.raises(ExtractionError) as e:
            vlmd_extract(input_file, test_title, output_type="csv")
        assert fail_message in str(e.value)


def test_extract_invalid_converted_data():
    # convert csv to invalid json
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    fail_message = "Failed extraction"

    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.side_effect = ExtractionError(fail_message)
        with pytest.raises(ExtractionError) as e:
            vlmd_extract(input_file, test_title, output_type="json")
        assert fail_message in str(e.value)

    # convert json to invalid csv
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.side_effect = ExtractionError(fail_message)
        with pytest.raises(ExtractionError) as e:
            vlmd_extract(input_file, test_title, output_type="csv")
        assert fail_message in str(e.value)
