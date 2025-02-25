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
    """Extract various valid input types"""
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    expected_file_name = f"{tmp_path}/{OUTPUT_FILE_PREFIX}_vlmd_valid.{output_type}"

    result = vlmd_extract(
        input_file, title=test_title, output_dir=tmp_path, output_type=output_type
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
    """Invalid input triggers error"""
    with pytest.raises(error_type) as err:
        vlmd_extract(input_file, test_title)
    assert expected_message in str(err.value)


def test_extract_unallowed_input_type():
    """Unallowed input type triggers error"""
    input_file = "tests/test_data/vlmd/invalid/vlmd_invalid.txt"
    with pytest.raises(ExtractionError) as err:
        vlmd_extract(input_file, test_title)
    expected_message = "Input file must be one of"
    assert expected_message in str(err.value)


def test_extract_unallowed_file_type():
    """Unallowed file type triggers error"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    with pytest.raises(ExtractionError) as err:
        vlmd_extract(input_file, title=test_title, file_type="txt")
    expected_message = "File type must be one of"
    assert expected_message in str(err.value)


def test_extract_input_does_not_exist(tmp_path):
    """Input file does-not-exist triggers error"""
    input_file = f"{tmp_path}/foo.csv"
    with pytest.raises(ExtractionError) as err:
        vlmd_extract(input_file, test_title)
    expected_message = f"Input file does not exist: {input_file}"
    assert expected_message in str(err.value)


def test_extract_unallowed_output():
    """Unallowed output type triggers error"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    unallowed_output = "txt"
    with pytest.raises(ExtractionError) as err:
        vlmd_extract(
            input_file, title=test_title, file_type="json", output_type=unallowed_output
        )
    expected_message = f"Unrecognized output_type '{unallowed_output}' - should be in {ALLOWED_OUTPUT_TYPES}"
    assert expected_message in str(err.value)


def test_extract_missing_title():
    """
    Title should be supplied when converting from non-json to json,
    unless the data contains standardsMappings.instrument.title
    """
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.return_value = {
            "schemaVersion": "0.3.2",
            "title": "default title from config - not a user supplied title",
            "fields": [],
        }
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(input_file, file_type="csv", output_type="json")
    expected_message = "Title must be supplied when extracting from non-json to json"
    assert expected_message in str(err.value)


def test_get_title_from_standards_mapping(tmp_path):
    """
    If a CSV input has standardsMapping.title then use that
    for title and don't raise an error
    """
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    output_file_name = f"{tmp_path}/output_with_title"
    test_title = "Instrument Test Title"
    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate, patch(
        "heal.vlmd.extract.extract.get_output_filepath"
    ) as mock_output_filepath:
        # converted CSV has a standardsMappings title
        # and a default title from config
        mock_validate.return_value = {
            "schemaVersion": "0.3.2",
            "title": "default title from config - not a user supplied title",
            "standardsMappings": [
                {
                    "instrument": {
                        "title": test_title,
                        "id": "1234",
                        "url": "https://theurl",
                    }
                }
            ],
            "fields": [],
        }
        mock_output_filepath.return_value = output_file_name
        # call extract without title - get title from standardsMappings
        result = vlmd_extract(input_file, file_type="csv", output_type="json")
        assert result
        assert os.path.isfile(output_file_name)
        with open(output_file_name, "r") as json_file:
            data = json.load(json_file)
        assert "standardsMappings" in data.keys()
        assert data["title"] == test_title

        # call extract with a title so we don't use the standardsMappings title
        result = vlmd_extract(
            input_file, title="Some other title", file_type="csv", output_type="json"
        )
        assert result
        assert os.path.isfile(output_file_name)
        with open(output_file_name, "r") as json_file:
            data = json.load(json_file)
        assert "standardsMappings" in data.keys()
        assert data["title"] == "Some other title"


def test_extract_failed_dict_write():
    """Failed conversion should trigger error"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    fail_message = "Error in writing converted dictionary"
    with patch("heal.vlmd.extract.extract.write_vlmd_dict") as mock_write:
        mock_write.side_effect = Exception("some exception")
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(input_file, title=test_title, output_type="csv")
        assert fail_message in str(err.value)


def test_extract_invalid_converted_data():
    """Invalid converted data should trigger error"""
    # convert csv to invalid json
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    fail_message = "Failed extraction"

    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.side_effect = ExtractionError(fail_message)
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(input_file, title=test_title, output_type="json")
        assert fail_message in str(err.value)

    # convert json to invalid csv
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.side_effect = ExtractionError(fail_message)
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(input_file, title=test_title, output_type="csv")
        assert fail_message in str(err.value)
