import os
from unittest.mock import patch

from click.testing import CliRunner
import pytest

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
        "--input_file PATH   name of file to extract HEAL-compliant VLMD file",
        "--file_type TEXT    Type of input file: auto, csv, json, tsv, dataset_csv",
        "                    dataset_tsv, redcap  [default: auto]",
        "--title TEXT        Root level title for the dictionary (required if",
        "--output_dir PATH   directory to write converted dictionary  [default: .]",
        "--output_type TEXT  File type(s) for extracted dictionary. Single value (csv),",
        "                    or comma separated values ('csv,json')  [default: json]",
    ]
    result = runner.invoke(cli_module.main, ["vlmd", "extract", "--help"])

    assert result.exit_code == 0
    assert expected_text in result.output
    for command_text in expected_commands:
        assert command_text in result.output


@pytest.mark.parametrize(
    "test_output_type, expected_output_type",
    [
        ("csv", ["csv"]),
        ("json", ["json"]),
        ("csv,json", ["csv", "json"]),
        (None, ["json"]),
    ],
)
def test_extract_valid_input(tmp_path, test_output_type, expected_output_type):
    """
    Test the cli extract with a valid input file.
    'file_type' parameter should default to 'auto'.
    """
    runner = CliRunner()
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    title = "Test dictionary"
    cli_args = [
        "vlmd",
        "extract",
        "--input_file",
        input_file,
        "--title",
        title,
        "--output_dir",
        tmp_path,
    ]
    with patch("heal.cli.vlmd.extract.vlmd_extract") as mock_vlmd_extract:
        mock_vlmd_extract.return_value = True
        if test_output_type:
            cli_args.append("--output_type")
            cli_args.append(test_output_type)

        result = runner.invoke(cli_module.main, cli_args)

    assert result.exit_code == 0
    mock_vlmd_extract.assert_called_once_with(
        input_file,
        title=title,
        file_type="auto",
        output_dir=tmp_path,
        output_type=expected_output_type,
    )


def test_extract_dataset_csv(tmp_path):
    """
    Test the cli extract with a 'dataset_csv' file type.
    'output_type' should default to 'json'.
    """
    runner = CliRunner()
    input_file = "tests/test_data/vlmd/valid/vlmd_valid_data.csv"
    title = "Test dictionary"
    file_type = "dataset_csv"

    with patch("heal.cli.vlmd.extract.vlmd_extract") as mock_vlmd_extract:
        mock_vlmd_extract.return_value = True
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
    mock_vlmd_extract.assert_called_once_with(
        input_file,
        title=title,
        file_type=file_type,
        output_dir=tmp_path,
        output_type=["json"],
    )


def test_extract_missing_input_file(tmp_path):
    """Test the cli extract"""
    runner = CliRunner()
    result = runner.invoke(
        cli_module.main,
        ["vlmd", "extract", "--output_dir", tmp_path],
    )
    assert result.exit_code != 0


def test_extract_invalid_output_type(tmp_path):
    """Test the cli extract with invalid output_type raises click.BadParameter"""
    runner = CliRunner()
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    title = "Test dictionary"

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
            "--output_type",
            "invalid_type",
        ],
    )

    assert result.exit_code != 0
    assert "Invalid value for '--output_type'" in result.output
    assert "invalid_type" in result.output


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
    result = runner.invoke(cli_module.main, ["vlmd", "validate"])
    assert result.exit_code != 0
