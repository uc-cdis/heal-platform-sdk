import csv
import json
import os
from unittest.mock import patch

import pytest

from heal.vlmd.config import ALLOWED_OUTPUT_TYPES, OUTPUT_FILE_PREFIX, TOP_LEVEL_PROPS
from heal.vlmd.extract.csv_dict_conversion import RedcapExtractionError
from heal.vlmd.extract.extract import (
    ExtractionError,
    set_title_if_missing,
    vlmd_extract,
)


@pytest.fixture(name="test_title")
def fixture_test_title():
    """String for dictionary title"""
    return "Test title for unit tests"


@pytest.mark.parametrize(
    "input_file_name, file_type",
    [
        ("vlmd_valid.csv", "csv"),
        ("vlmd_valid.json", "json"),
        ("vlmd_valid.tsv", "tsv"),
        ("vlmd_valid_data.csv", "dataset_csv"),
        ("vlmd_valid_data.tsv", "dataset_tsv"),
    ],
)
def test_extract_valid_input_json_output(
    input_file_name, file_type, test_title, tmp_path
):
    """Extract various valid input types without error and write result to json file"""

    output_type = "json"
    if file_type in ["dataset_csv", "dataset_tsv"]:
        # subset of standard dictionary fields keys
        expected_fields = ["name", "description", "type"]
    else:
        # larger subset of standard dictionary fields keys
        expected_fields = ["section", "name", "title", "description", "type"]
    input_file_path = f"tests/test_data/vlmd/valid/{input_file_name}"
    root_name, _ = os.path.splitext(input_file_name)
    expected_file_name = f"{tmp_path}/{OUTPUT_FILE_PREFIX}_{root_name}.{output_type}"

    result = vlmd_extract(
        input_file_path, title=test_title, output_dir=tmp_path, output_type=output_type
    )

    assert result
    assert os.path.isfile(expected_file_name)
    with open(expected_file_name, "r") as json_file:
        data = json.load(json_file)
    assert "schemaVersion" in data.keys()
    assert "fields" in data.keys()
    assert set(expected_fields).issubset(list(data["fields"][0].keys()))


@pytest.mark.parametrize(
    "input_file_name",
    [
        "vlmd_valid.csv",
        "vlmd_valid.json",
        "vlmd_valid.tsv",
        "vlmd_valid_data.csv",
        "vlmd_valid_data.tsv",
    ],
)
def test_extract_valid_input_csv_output(input_file_name, test_title, tmp_path):
    """Extract various valid input types without error and write result to csv file"""

    output_type = "csv"
    expected_fields = ["schemaVersion", "name", "title", "description", "type"]
    input_file_path = f"tests/test_data/vlmd/valid/{input_file_name}"
    root_name, _ = os.path.splitext(input_file_name)
    expected_file_name = f"{tmp_path}/{OUTPUT_FILE_PREFIX}_{root_name}.{output_type}"

    result = vlmd_extract(
        input_file_path, title=test_title, output_dir=tmp_path, output_type=output_type
    )

    assert result
    assert os.path.isfile(expected_file_name)
    with open(expected_file_name, "r") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)
        print(f"Expected fields {expected_fields}")
        print(f"header {header}")
        assert set(expected_fields).issubset(header)


@pytest.mark.parametrize("file_type", ["dataset_csv", "dataset_tsv"])
def test_extract_dataset_auto_with_fallback(
    file_type, valid_converted_csv_dataset_to_json, test_title, tmp_path
):
    """
    With file_type = "auto" the dataset extraction will first process the input
    as a csv dictionary with vlmd_validate. The validation should raise an error.
    Extract will fall back to processing input as a dataset using convert_to_vlmd.
    """

    output_type = "json"
    suffix = file_type.split("_")[-1]
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid_data.{suffix}"
    expected_file_name = (
        f"{tmp_path}/{OUTPUT_FILE_PREFIX}_vlmd_valid_data.{output_type}"
    )

    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        fail_message = "'description' is a required property"
        mock_validate.side_effect = ExtractionError(fail_message)
        mock_validate.return_value = {
            "schemaVersion": "0.3.2",
            "title": "some_title",
            "fields": [],
        }
        with patch("heal.vlmd.extract.extract.convert_to_vlmd") as mock_convert:
            mock_convert.return_value = {
                "template_json": valid_converted_csv_dataset_to_json
            }

            result = vlmd_extract(
                input_file,
                title=test_title,
                file_type="auto",
                output_dir=tmp_path,
                output_type="json",
            )
            mock_validate.assert_called()
            # Test that validate was called with file_type="csv"
            mock_validate.assert_called_with(
                input_file,
                file_type=suffix,
                output_type="json",
                return_converted_output=True,
            )
            # Test that convert_to_vlmd was called with dataset input type
            # ie, we did a fallback to dataset after trying dictionary
            mock_convert.assert_called_with(
                input_filepath=input_file,
                input_type="csv-data-set",
                data_dictionary_props={},
                include_all_fields=True,
            )

    assert result
    assert os.path.isfile(expected_file_name)
    with open(expected_file_name, "r") as f:
        data = json.load(f)
    assert "fields" in data.keys()
    assert "schemaVersion" in data.keys()
    assert data == valid_converted_csv_dataset_to_json


@pytest.mark.parametrize("file_type", ["csv", "tsv"])
def test_extract_dict_auto_without_fallback(
    file_type, valid_converted_csv_to_json, test_title, tmp_path
):
    """
    With file_type = "auto" the dictionary extraction will first process the input
    as a csv dictionary. The validation should not raise an error. Extract will
    not fall back to trying input as a dataset.
    """

    output_type = "json"
    input_file = f"tests/test_data/vlmd/valid/vlmd_valid.{file_type}"
    expected_file_name = f"{tmp_path}/{OUTPUT_FILE_PREFIX}_vlmd_valid.{output_type}"
    # expected output is valid csv dictionary converted to json.
    expected_valid_data = {
        "schemaVersion": "0.3.2",
        "title": "some title",
        "fields": valid_converted_csv_to_json["fields"],
    }

    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.return_value = expected_valid_data
        with patch("heal.vlmd.extract.extract.convert_to_vlmd") as mock_convert:
            mock_convert.return_value = {
                "template_json": {
                    "schemaVersion": "0.3.2",
                    "title": "some other title",
                    "fields": [],
                }
            }

            result = vlmd_extract(
                input_file,
                title=test_title,
                file_type="auto",
                output_dir=tmp_path,
                output_type="json",
            )
            mock_validate.assert_called()
            # Test that validate was called with file_type="csv"
            mock_validate.assert_called_with(
                input_file,
                file_type=file_type,
                output_type=output_type,
                return_converted_output=True,
            )
            # Test that convert_to_vlmd was not called
            # ie, no fallback after successful dictionary validation.
            mock_convert.assert_not_called()

    assert result
    assert os.path.isfile(expected_file_name)
    with open(expected_file_name, "r") as f:
        data = json.load(f)
    assert "fields" in data.keys()
    assert "schemaVersion" in data.keys()
    assert data == expected_valid_data


def test_extract_invalid_redcap_auto_without_fallback(test_title, tmp_path):
    """
    With file_type = "auto" the dictionary extraction will first process the input
    as a csv dictionary. An invalid REDCap dictionary will trigger an error.
    There is no fallback to dataset because the input is known to be a REDCap dictionary.
    """

    output_type = "json"
    input_file = "tests/test_data/vlmd/invalid/vlmd_redcap_checkbox_unfilled.csv"
    expected_file_name = (
        f"{tmp_path}/{OUTPUT_FILE_PREFIX}_vlmd_redcap_checkbox_unfilled.{output_type}"
    )

    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        fail_message = "REDCap conversion error for mapping field 'aerobics'"
        mock_validate.side_effect = RedcapExtractionError(fail_message)
        with patch("heal.vlmd.extract.extract.convert_to_vlmd") as mock_convert:
            mock_convert.return_value = {"some": "data"}

            with pytest.raises(ExtractionError) as err:
                vlmd_extract(
                    input_file,
                    title=test_title,
                    file_type="auto",
                    output_dir=tmp_path,
                    output_type="json",
                )

                mock_validate.assert_called_with(
                    input_file,
                    file_type="csv",
                    output_type=output_type,
                    return_converted_output=True,
                )
                # Test that convert_to_vlmd was not called
                # ie, no fallback after unsuccessful REDCap dictionary validation.
                mock_convert.assert_not_called()

    assert not os.path.isfile(expected_file_name)


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
        (
            "tests/test_data/vlmd/invalid/vlmd_redcap_checkbox_unfilled.csv",
            "REDCap conversion error for mapping field 'aerobics'",
            ExtractionError,
        ),
    ],
)
def test_extract_invalid_input(input_file, expected_message, error_type, test_title):
    """Invalid input triggers error"""
    with pytest.raises(error_type) as err:
        vlmd_extract(input_file, title=test_title, file_type="csv")
    assert expected_message in str(err.value)


def test_extract_unallowed_input_type(test_title):
    """Unallowed input type triggers error"""
    input_file = "tests/test_data/vlmd/invalid/vlmd_invalid.txt"
    with pytest.raises(ExtractionError) as err:
        vlmd_extract(input_file, test_title)
    expected_message = "Input file must be one of"
    assert expected_message in str(err.value)


def test_extract_unallowed_file_type(test_title):
    """Unallowed file type triggers error"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    with pytest.raises(ExtractionError) as err:
        vlmd_extract(input_file, title=test_title, file_type="txt")
    expected_message = "File type must be one of"
    assert expected_message in str(err.value)


def test_extract_input_does_not_exist(test_title, tmp_path):
    """Input file does-not-exist triggers error"""
    input_file = f"{tmp_path}/foo.csv"
    with pytest.raises(ExtractionError) as err:
        vlmd_extract(input_file, test_title)
    expected_message = f"Input file does not exist: {input_file}"
    assert expected_message in str(err.value)


def test_extract_unallowed_output(test_title):
    """Unallowed output type triggers error"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    unallowed_output = "txt"
    with pytest.raises(ExtractionError) as err:
        vlmd_extract(
            input_file, title=test_title, file_type="json", output_type=unallowed_output
        )
    expected_message = f"Unrecognized output_type '{unallowed_output}' - should be in {ALLOWED_OUTPUT_TYPES}"
    assert expected_message in str(err.value)


@pytest.mark.parametrize(
    "test_dict_title",
    [
        (""),
        ("   "),
        ("\n"),
        ("\t"),
    ],
)
def test_extract_empty_title(test_dict_title):
    """Empty title should trigger error"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    fail_message = "Empty title is not allowed"

    with pytest.raises(ExtractionError) as err:
        vlmd_extract(input_file, title=test_dict_title, output_type="csv")
    assert fail_message in str(err.value)


def test_extract_missing_title(test_title):
    """
    Title should be supplied when converting from non-json to json,
    unless the data contains standardsMappings.instrument.title
    """
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    default_csv_title = TOP_LEVEL_PROPS.get("title")

    # missing standardsMapping
    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.return_value = {
            "schemaVersion": "0.3.2",
            "title": default_csv_title,
            "fields": [],
        }
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(input_file, file_type="csv", output_type="json")
    expected_message = "Title must be supplied when extracting from non-json to json"
    assert expected_message in str(err.value)

    # have standardsMapping, but no instrument
    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.return_value = {
            "schemaVersion": "0.3.2",
            "title": default_csv_title,
            "standardsMappings": [
                {
                    "some other field, not instrument": {
                        "title": test_title,
                        "id": "1234",
                        "url": "https://theurl",
                    }
                }
            ],
            "fields": [],
        }
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(input_file, file_type="csv", output_type="json")
    expected_message = "Title must be supplied when extracting from non-json to json"
    assert expected_message in str(err.value)


def test_get_title_from_standards_mapping(tmp_path):
    """
    If a CSV input has standardsMapping.instrument.title then use that
    for title and don't raise an error
    """
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    output_file_name = f"{tmp_path}/output_with_title"
    instrument_title = "Instrument Test Title"
    default_csv_title = TOP_LEVEL_PROPS.get("title")

    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate, patch(
        "heal.vlmd.extract.extract.get_output_filepath"
    ) as mock_output_filepath:
        # converted CSV has a standardsMappings title
        # and a default title from config
        mock_validate.return_value = {
            "schemaVersion": "0.3.2",
            "title": default_csv_title,
            "standardsMappings": [
                {
                    "instrument": {
                        "title": instrument_title,
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
        assert data["title"] == instrument_title
        assert data["title"] != default_csv_title

        # call extract with another title but it does not overwrite the standardsMappings title
        result = vlmd_extract(
            input_file, title="Some other title", file_type="csv", output_type="json"
        )
        assert result
        assert os.path.isfile(output_file_name)
        with open(output_file_name, "r") as json_file:
            data = json.load(json_file)
        assert "standardsMappings" in data.keys()
        assert data["title"] == instrument_title
        assert data["title"] != "Some other title"
        assert data["title"] != default_csv_title


def test_extract_failed_dict_write(test_title):
    """Failed conversion should trigger error"""
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    fail_message = "Error in writing converted dictionary"
    with patch("heal.vlmd.extract.extract.write_vlmd_dict") as mock_write:
        mock_write.side_effect = Exception("some exception")
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(input_file, title=test_title, output_type="csv")
        assert fail_message in str(err.value)


def test_extract_invalid_converted_data(test_title):
    """Invalid converted data should trigger error"""
    # convert csv to invalid json
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    fail_message = "Failed extraction"

    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.side_effect = ExtractionError(fail_message)
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(
                input_file, file_type="csv", title=test_title, output_type="json"
            )
        assert fail_message in str(err.value)

    # convert json to invalid csv
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    with patch("heal.vlmd.extract.extract.vlmd_validate") as mock_validate:
        mock_validate.side_effect = ExtractionError(fail_message)
        with pytest.raises(ExtractionError) as err:
            vlmd_extract(
                input_file, file_type="csv", title=test_title, output_type="csv"
            )
        assert fail_message in str(err.value)


@pytest.mark.parametrize(
    "converted_dict, title, expected_title",
    [
        (
            {
                "schemaVersion": "0.3.2",
                "fields": [],
            },
            "New title",
            "New title",
        ),
        (
            {
                "schemaVersion": "0.3.2",
                "title": "old title",
                "fields": [],
            },
            "New title",
            "old title",
        ),
        (
            {
                "schemaVersion": "0.3.2",
                "standardsMappings": [
                    {
                        "instrument": {
                            "title": "standardsMappings title",
                            "id": "1234",
                            "url": "https://theurl",
                        }
                    }
                ],
                "fields": [],
            },
            None,
            "standardsMappings title",
        ),
        (
            {
                "schemaVersion": "0.3.2",
                "title": "old title",
                "standardsMappings": [
                    {
                        "instrument": {
                            "title": "standardsMappings title",
                            "id": "1234",
                            "url": "https://theurl",
                        }
                    }
                ],
                "fields": [],
            },
            None,
            "standardsMappings title",
        ),
        (
            {
                "schemaVersion": "0.3.2",
                "title": "old title",
                "standardsMappings": [
                    {
                        "instrument": {
                            "title": "standardsMappings title",
                            "id": "1234",
                            "url": "https://theurl",
                        }
                    }
                ],
                "fields": [],
            },
            "New title",
            "standardsMappings title",
        ),
    ],
)
def test_set_title_if_missing(converted_dict, title, expected_title):
    """Test that set_title uses title or standardsMapping"""
    new_dict = set_title_if_missing(
        file_type="csv", title=title, converted_dict=converted_dict
    )
    assert new_dict.get("title") == expected_title
