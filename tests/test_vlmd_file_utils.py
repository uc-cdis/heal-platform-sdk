from heal.vlmd.config import OUTPUT_FILE_PREFIX
from heal.vlmd.file_utils import get_output_filepath, write_vlmd_dict


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
