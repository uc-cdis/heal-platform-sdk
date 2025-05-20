import pytest

from heal.vlmd.extract.csv_data_conversion import convert_dataset_csv


def test_convert_dataset_csv(valid_converted_csv_dataset_to_json):
    input_file = "tests/test_data/vlmd/valid/vlmd_valid_data.csv"
    # this fixture has a superset of fields that we trim below
    expected_data = valid_converted_csv_dataset_to_json["fields"]

    package = convert_dataset_csv(input_file)

    # convert generates json
    assert "template_json" in package
    assert "fields" in package["template_json"]
    for field in expected_data:
        # get the subset of inferred fields
        subset_field = {
            k: v for k, v in field.items() if k in ["name", "type", "constraints"]
        }
        assert subset_field in package["template_json"]["fields"]
