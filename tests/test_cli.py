import os

from click.testing import CliRunner

import heal.cli.heal_cli as cli_module
import heal.vlmd.file_utils as file_utils


def test_help():
    """Test the help menu"""
    runner = CliRunner()
    expected_text = "HEAL-Platform SDK Command Line Interface"
    expected_commands = ["vlmd  Commands for VLMD"]
    result = runner.invoke(cli_module.main, ["--help"])
    assert result.exit_code == 0
    assert expected_text in result.output
    for command_text in expected_commands:
        assert command_text in result.output


def test_vlmd_help():
    """Test the VLMD submenu"""
    runner = CliRunner()
    expected_text = "Commands for VLMD"
    expected_commands = [
        "extract   Extract HEAL-compliant VLMD file from input file",
        "validate  Validate VLMD input file",
    ]
    result = runner.invoke(cli_module.main, ["vlmd", "--help"])
    assert result.exit_code == 0
    assert expected_text in result.output
    for command_text in expected_commands:
        assert command_text in result.output


def test_extract_help():
    """Test the extract submenu"""
    runner = CliRunner()
    expected_text = "Extract HEAL-compliant VLMD file from input file"
    # truncated to avoid wrapped lines
    expected_commands = [
        "--input_file PATH  name of file to extract HEAL-compliant VLMD file",
        "--file_type TEXT   Type of input file: auto, csv, json, tsv, dataset_csv",
        "                   dataset_tsv, redcap  [default: auto]",
        "--title TEXT       Root level title for the dictionary (required if",
        "--output_dir PATH  directory to write converted dictionary'  [default: .]",
    ]
    result = runner.invoke(cli_module.main, ["vlmd", "extract", "--help"])
    assert result.exit_code == 0
    assert expected_text in result.output
    for command_text in expected_commands:
        assert command_text in result.output


def test_extract(tmp_path):
    """Test the cli extract"""
    runner = CliRunner()
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    title = "Test dictionary"
    expected_output_file = file_utils.get_output_filepath(
        tmp_path, input_file, output_type="json"
    )
    result = runner.invoke(
        cli_module.main,
        [
            "vlmd",
            "extract",
            "--input_file",
            input_file,
            "--title",
            title,
            "--output_dir",
            tmp_path,
        ],
    )
    assert result.exit_code == 0
    assert os.path.isfile(expected_output_file)


def test_extract_dataset_csv(tmp_path):
    """Test the cli extract"""
    runner = CliRunner()
    input_file = "tests/test_data/vlmd/valid/vlmd_valid_data.csv"
    title = "Test dictionary"
    file_type = "dataset_csv"
    expected_output_file = file_utils.get_output_filepath(
        tmp_path, input_file, output_type="json"
    )
    result = runner.invoke(
        cli_module.main,
        [
            "vlmd",
            "extract",
            "--input_file",
            input_file,
            "--file_type",
            file_type,
            "--title",
            title,
            "--output_dir",
            tmp_path,
        ],
    )
    assert result.exit_code == 0
    assert os.path.isfile(expected_output_file)


def test_extract_missing_input_file(tmp_path):
    """Test the cli extract"""
    runner = CliRunner()
    input_file = None
    result = runner.invoke(
        cli_module.main,
        ["vlmd", "extract", "--input_file", input_file, "--output_dir", tmp_path],
    )
    assert result.exit_code != 0


def test_validate_help():
    """Test the validate submenu"""
    runner = CliRunner()
    expected_text = "Validate VLMD input file"
    expected_commands = [
        "--input_file PATH  name of file to validate",
    ]
    result = runner.invoke(cli_module.main, ["vlmd", "validate", "--help"])
    assert result.exit_code == 0
    assert expected_text in result.output
    for command_text in expected_commands:
        assert command_text in result.output


def test_validate(tmp_path):
    """Test the cli validation"""
    runner = CliRunner()
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    result = runner.invoke(
        cli_module.main, ["vlmd", "validate", "--input_file", input_file]
    )
    assert result.exit_code == 0


def test_validate_missing_input_file(tmp_path):
    """Test the cli validation"""
    runner = CliRunner()
    input_file = None
    result = runner.invoke(
        cli_module.main, ["vlmd", "validate", "--input_file", input_file]
    )
    assert result.exit_code != 0
