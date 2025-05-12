from unittest.mock import patch

import pytest

from heal.vlmd.extract.redcap_csv_dict_conversion import (
    _add_description,
    _add_title,
    convert_redcap_csv,
    gather,
    read_from_file,
    rename_and_fill,
)

VALID_REDCAP_SOURCE_FIELDS = [
    {
        "name": "study_id",
        "form": "demographics",
        "section": "",
        "type": "text",
        "label": "Study ID",
        "choice_calc_lbls": "",
        "note": "",
        "text_valid_slider_num": "",
        "text_valid_min": "",
        "text_valid_max": "",
        "identifier": "",
        "skip_logic": "",
        "required": "",
        "align": "",
        "question_num": "",
        "matrix_group": "",
    },
    {
        "name": "date_enrolled",
        "form": "demographics",
        "section": "Demographic Characteristics",
        "type": "text",
        "label": "Date subject signed consent",
        "choice_calc_lbls": "",
        "note": "YYYY-MM-DD",
        "text_valid_slider_num": "date",
        "text_valid_min": "",
        "text_valid_max": "",
        "identifier": "",
        "skip_logic": "",
        "required": "",
        "align": "",
        "question_num": "",
        "matrix_group": "",
    },
    {
        "name": "email",
        "form": "demographics",
        "section": "Demographic Characteristics",
        "type": "text",
        "label": "E-mail",
        "choice_calc_lbls": "",
        "note": "",
        "text_valid_slider_num": "email",
        "text_valid_min": "",
        "text_valid_max": "",
        "identifier": "",
        "skip_logic": "",
        "required": "",
        "align": "",
        "question_num": "",
        "matrix_group": "",
    },
    {
        "name": "sex",
        "form": "demographics",
        "section": "Demographic Characteristics",
        "type": "dropdown",
        "label": "Gender",
        "choice_calc_lbls": "0, Female | 1, Male",
        "note": "",
        "text_valid_slider_num": "",
        "text_valid_min": "",
        "text_valid_max": "",
        "identifier": "",
        "skip_logic": "",
        "required": "",
        "align": "",
        "question_num": "",
        "matrix_group": "",
    },
    {
        "name": "height",
        "form": "demographics",
        "section": "Demographic Characteristics",
        "type": "number",
        "label": "Gender",
        "choice_calc_lbls": "0, Female | 1, Male",
        "note": "",
        "text_valid_slider_num": "",
        "text_valid_min": "130",
        "text_valid_max": "215",
        "identifier": "",
        "skip_logic": "",
        "required": "",
        "align": "",
        "question_num": "",
        "matrix_group": "",
    },
]


def test_rename_and_fill():
    """Test rename_and_fill"""

    input_path = "tests/test_data/vlmd/valid/vlmd_redcap_dict_small.csv"
    expected_renamed_columns = VALID_REDCAP_SOURCE_FIELDS[0].keys()

    # read the test file
    source_dataframe = read_from_file(input_path)
    # pass the dataframe to 'rename_and_fill'
    source_data_table = rename_and_fill(source_dataframe)

    assert set(source_data_table[0].keys()) == set(expected_renamed_columns)

    for record in source_data_table:
        if record["name"] == "study_id":
            assert record["type"] == "text"
            assert record["text_valid_slider_num"] == ""
        if record["name"] == "date_enrolled":
            assert record["type"] == "text"
            assert record["text_valid_slider_num"] == "date"
        if record["name"] == "email":
            assert record["type"] == "text"
            assert record["text_valid_slider_num"] == "email"
        if record["name"] == "sex":
            assert record["type"] == "dropdown"
            assert record["text_valid_slider_num"] == ""
            assert record["choice_calc_lbls"] == "0, Female | 1, Male"


def test_gather():
    """Test gather"""

    expected_target_fields = [
        "name",
        "type",
        "description",
        "title",
        "section",
        "constraints",
    ]

    target_fields = gather(VALID_REDCAP_SOURCE_FIELDS)
    # check keys
    assert set(target_fields[0].keys()) == set(expected_target_fields)

    # check some values
    for record in target_fields:
        if record["name"] == "study_id":
            assert record["type"] == "string"
        if record["name"] == "date_enrolled":
            assert record["type"] == "date"
            assert record["format"] == "any"
        if record["name"] == "email":
            assert record["type"] == "string"
            assert record["format"] == "email"
        if record["name"] == "sex":
            assert record["type"] == "integer"
            assert record["enumLabels"] == {"0": "Female", "1": "Male"}
            assert record["constraints"] == {"enum": ["0", "1"]}
        if record["name"] == "height":
            assert record["type"] == "number"
            assert record["constraints"] == {"min": 130.0, "max": 215.0}
    pass


def test_convert_redcap_csv_bad_input():
    """Test the converter with input that is not path or dataframe"""
    unallowed_input = ["some", "random", "list"]
    with pytest.raises(ValueError) as err:
        convert_redcap_csv(unallowed_input)

    expected_message = (
        "Input should be either dataframe or path to REDCap dictionary csv export"
    )
    assert expected_message in str(err.value)


def test_gather_failed_mapping():
    """
    Test that convert raises a ValueError on failed mapping.
    Here, mock will trigger an error on the first field of the input source fields.
    """
    first_field = VALID_REDCAP_SOURCE_FIELDS[0]["name"]
    expected_message = f"REDCap conversion error for mapping field '{first_field}'"
    with patch(
        "heal.vlmd.extract.redcap_csv_dict_conversion._add_metadata"
    ) as mock_mappings:
        mock_mappings.side_effect = Exception("some mapping exception")
        with pytest.raises(ValueError) as err:
            result = gather(VALID_REDCAP_SOURCE_FIELDS)

        mock_mappings.assert_called()
        assert expected_message in str(err.value)


@pytest.mark.parametrize(
    "source_field, target_field, expected_description",
    [
        (
            {
                "name": "height",
                "section": "Demographics",
                "label": "Source Height (cm)",
            },
            {"type": "number", "description": "Subject height"},
            "Demographics: Source Height (cm)Subject height",
        ),
        (
            {
                "name": "height",
                "section": "Demographics",
                "label": "Source Height (cm)",
            },
            {
                "type": "number",
            },
            "Demographics: Source Height (cm)",
        ),
        (
            {"name": "height", "label": "Source Height (cm)"},
            {"type": "number", "description": "Subject height"},
            "Source Height (cm)Subject height",
        ),
        ({"name": "height"}, {"type": "number"}, "No field label for this variable"),
    ],
)
def test_add_description(source_field, target_field, expected_description):
    """Test the add_title method"""
    assert _add_description(source_field, target_field) == expected_description


@pytest.mark.parametrize(
    "source_field, target_field, expected_title",
    [
        (
            {"name": "height", "label": "Source Height (cm)"},
            {"type": "number"},
            "Source Height (cm)",
        ),
        (
            {"name": "height", "label": "Height (cm)"},
            {"type": "number", "title": "Target Height (cm)"},
            "Target Height (cm)",
        ),
        ({"name": "height"}, {"type": "number"}, "No field label for this variable"),
    ],
)
def test_add_title(source_field, target_field, expected_title):
    """Test the add_title method"""
    assert _add_title(source_field, target_field) == expected_title
