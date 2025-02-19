import pytest

from heal.vlmd.mappings.redcap_csv_headers import (
    choices_field_name,
    choices_label_input,
)
from heal.vlmd.mappings.redcap_field_mapping import (
    _parse_field_properties_from_encodings,
    map_checkbox,
    map_dropdown,
    map_radio,
    map_text,
)


def test_parse_field_properties():
    """Test mapping function parse_field_properties_from_encodings"""
    encodings_string = "0, No | 1, Yes"
    expected_dict = {
        "type": "integer",
        "enumLabels": {"0": "No", "1": "Yes"},
        "constraints": {"enum": ["0", "1"]},
    }
    assert _parse_field_properties_from_encodings(encodings_string) == expected_dict


@pytest.mark.parametrize(
    "input_string, expected_output_dict",
    [
        (
            {
                "name": "some_field_name",
                "text_valid_slider_num": "date",
                "text_valid_min": "",
            },
            {
                "type": "date",
                "format": "any",
                "constraints": {"pattern": None, "minimum": None, "maximum": None},
            },
        ),
        (
            {"name": "some_field_name", "text_valid_slider_num": ""},
            {
                "type": "string",
                "constraints": {"pattern": None, "minimum": None, "maximum": None},
            },
        ),
        (
            {"text_valid_slider_num": "email"},
            {
                "type": "string",
                "format": "email",
                "constraints": {"pattern": None, "minimum": None, "maximum": None},
            },
        ),
        (
            {
                "text_valid_slider_num": "integer",
                "text_valid_min": "0",
                "text_valid_max": "9",
            },
            {
                "type": "integer",
                "constraints": {"pattern": None, "minimum": 0, "maximum": 9},
            },
        ),
        (
            {"text_valid_slider_num": "alpha_only"},
            {
                "type": "string",
                "constraints": {
                    "pattern": "^[a-zA-Z]+$",
                    "minimum": None,
                    "maximum": None,
                },
            },
        ),
        (
            {
                "text_valid_slider_num": "number",
                "text_valid_min": "1.1",
                "text_valid_max": "2.2",
            },
            {
                "type": "number",
                "constraints": {"pattern": None, "minimum": 1.1, "maximum": 2.2},
            },
        ),
        (
            {"text_valid_slider_num": "phone"},
            {
                "type": "string",
                "constraints": {
                    "pattern": "^[0-9]{3}-[0-9]{3}-[0-9]{4}$",
                    "minimum": None,
                    "maximum": None,
                },
            },
        ),
        (
            {"text_valid_slider_num": "zipcode"},
            {
                "type": "string",
                "constraints": {
                    "pattern": "^[0-9]{5}$",
                    "minimum": None,
                    "maximum": None,
                },
            },
        ),
    ],
)
def test_map_text(input_string, expected_output_dict):
    """Test mapping function map_text"""
    assert map_text(input_string) == expected_output_dict


@pytest.mark.parametrize(
    "input_dict, expected_output_dict",
    [
        (
            {
                "text_valid_slider_num": "integer",
                "text_valid_min": "0",
                "text_valid_max": "[calculated_value]",
            },
            {
                "type": "integer",
                "constraints": {"pattern": None, "minimum": 0, "maximum": None},
            },
        ),
        (
            {
                "text_valid_slider_num": "number",
                "text_valid_min": "[calculated_value]",
                "text_valid_max": "2.2",
            },
            {
                "type": "number",
                "constraints": {"pattern": None, "minimum": None, "maximum": 2.2},
            },
        ),
        (
            {
                "text_valid_slider_num": "number, comma_decimal",
                "text_valid_min": "[calculated_value]",
                "text_valid_max": "2,2",
            },
            {
                "type": "number",
                "constraints": {"pattern": None, "minimum": None, "maximum": 2.2},
            },
        ),
    ],
)
def test_map_integer_skip_calc(input_dict, expected_output_dict):
    """Test that non-numeric (eg, calculated) min/max get skipped"""
    assert map_text(input_dict) == expected_output_dict


def test_map_dropdown_with_error():
    """Test that map_dropdown raises error with empty Choices field"""
    input_row = {
        "name": "some_field_name",
        choices_field_name: "",
    }
    expected_message = (
        "Missing value in dropdown field '"
        f"{input_row.get('name')}"
        f"' in column '{choices_label_input}'."
    )
    with pytest.raises(ValueError) as err:
        map_dropdown(input_row)
    assert expected_message in str(err.value)


def test_map_radio_with_error():
    """Test that map_radio raises error with empty Choices field"""
    input_row = {
        "name": "some_field_name",
        choices_field_name: "",
    }
    expected_message = (
        "Missing value in radio field '"
        f"{input_row.get('name')}"
        f"' in column '{choices_label_input}'."
    )
    with pytest.raises(ValueError) as err:
        map_radio(input_row)
    assert expected_message in str(err.value)


def test_map_checkbox():
    """Test the mapping of checkbox data into expanded list of bools"""
    input_dict = {
        "name": "gym",
        "type": "checkbox",
        "choice_calc_lbls": "0, Monday | 1, Tuesday",
    }
    expected_output_list = [
        {
            "description": "[choice=Monday]",
            "title": "Gym: Monday",
            "name": "gym___0",
            "type": "boolean",
            "constraints": {"enum": ["0", "1"]},
            "enumLabels": {"0": "Unchecked", "1": "Checked"},
        },
        {
            "description": "[choice=Tuesday]",
            "title": "Gym: Tuesday",
            "name": "gym___1",
            "type": "boolean",
            "constraints": {"enum": ["0", "1"]},
            "enumLabels": {"0": "Unchecked", "1": "Checked"},
        },
    ]
    assert map_checkbox(input_dict) == expected_output_list
