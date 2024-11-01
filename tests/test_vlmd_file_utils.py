import json
import os

import pandas as pd

from heal.vlmd.config import OUTPUT_FILE_PREFIX
from heal.vlmd.file_utils import get_output_filepath, write_vlmd_dict


def test_write_json(tmp_path, valid_json_data):
    output_filepath = f"{tmp_path}/some/path/valid_dict.json"
    if os.path.isfile(output_filepath):
        os.unlink(output_filepath)
    result = write_vlmd_dict(
        valid_json_data, output_filepath=output_filepath, file_type="json"
    )
    assert result

    with open(output_filepath, "r") as f:
        data = json.load(f)
    assert data == valid_json_data


def test_write_csv(tmp_path, valid_array_data):
    output_filepath = f"{tmp_path}/some/other/path/valid_dict.csv"
    if os.path.isfile(output_filepath):
        os.unlink(output_filepath)
    result = write_vlmd_dict(
        valid_array_data, output_filepath=output_filepath, file_type="csv"
    )
    assert result

    # reconstruct the array_data from the written csv
    df = pd.read_csv(output_filepath)
    df = df.fillna("")
    df["missingValues"] = df["missingValues"].astype(str).replace("99.0", "99")
    read_as_array = df.to_dict(orient="records")

    assert read_as_array == valid_array_data


def test_get_output_filepath():
    output_dir = "tmp/foo"
    input_filename = "data/valid/valid_dict.csv"
    output_type = "auto"
    expected_output_filepath = f"tmp/foo/{OUTPUT_FILE_PREFIX}_valid_dict.csv"
    result = get_output_filepath(output_dir, input_filename, output_type=output_type)
    assert result == expected_output_filepath

    output_type = "json"
    expected_output_filepath = f"tmp/foo/{OUTPUT_FILE_PREFIX}_valid_dict.json"
    result = get_output_filepath(output_dir, input_filename, output_type=output_type)
    assert result == expected_output_filepath


def test_write_vlmd_unallowed():
    dictionary = "some text"
    output_filepath = "tmp/foo/unallowed_suffix.txt"
    input_filename = "data/valid/unallowed_suffix.txt"
    result = write_vlmd_dict(
        dictionary, output_filepath=output_filepath, file_type="auto"
    )
    assert result == None
