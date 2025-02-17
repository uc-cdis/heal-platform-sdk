import pytest
from heal.vlmd.mappings.redcap_field_mapping import (
    _parse_field_properties_from_encodings,
    map_checkbox,
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
                "constraints": {"pattern": None, "min": None, "max": None},
            },
        ),
        (
            {"name": "some_field_name", "text_valid_slider_num": ""},
            {
                "type": "string",
                "constraints": {"pattern": None, "min": None, "max": None},
            },
        ),
        (
            {"text_valid_slider_num": "email"},
            {
                "type": "string",
                "format": "email",
                "constraints": {"pattern": None, "min": None, "max": None},
            },
        ),
        (
            {
                "text_valid_slider_num": "integer",
                "text_valid_min": "0",
                "text_valid_max": "9",
            },
            {"type": "integer", "constraints": {"pattern": None, "min": 0, "max": 9}},
        ),
        (
            {"text_valid_slider_num": "alpha_only"},
            {
                "type": "string",
                "constraints": {"pattern": "^[a-zA-Z]+$", "min": None, "max": None},
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
                "constraints": {"pattern": None, "min": 1.1, "max": 2.2},
            },
        ),
        (
            {"text_valid_slider_num": "phone"},
            {
                "type": "string",
                "constraints": {
                    "pattern": "^[0-9]{3}-[0-9]{3}-[0-9]{4}$",
                    "min": None,
                    "max": None,
                },
            },
        ),
        (
            {"text_valid_slider_num": "zipcode"},
            {
                "type": "string",
                "constraints": {"pattern": "^[0-9]{5}$", "min": None, "max": None},
            },
        ),
    ],
)
def test_map_text(input_string, expected_output_dict):
    """Test mapping function map_text"""
    assert map_text(input_string) == expected_output_dict


def test_map_dropdown_with_error():
    """Test that map_dropdown raises error with empty field"""

    pass


def test_map_radio_with_error():
    """Test that map_radio raises error with empty field"""

    pass


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
