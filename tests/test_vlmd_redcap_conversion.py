import pytest
from heal.vlmd.extract.redcap_csv_dict_conversion import (
    convert_redcap_csv,
    gather,
    read_from_file,
    rename_and_fill,
)

valid_redcap_source_fields = [
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
    expected_renamed_columns = valid_redcap_source_fields[0].keys()

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

    target_fields = gather(valid_redcap_source_fields)
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
