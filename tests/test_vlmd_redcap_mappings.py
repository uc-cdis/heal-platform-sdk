import pytest

from heal.vlmd.mappings.redcap_csv_headers import (
    CHOICES_FIELD_NAME,
    CHOICES_LABEL_INPUT,
)
from heal.vlmd.mappings.redcap_field_mapping import (
    _parse_field_properties_from_encodings,
    map_checkbox,
    map_dropdown,
    map_radio,
    map_text,
    map_slider,
)


@pytest.mark.parametrize(
    "test_encodings_string, expected_dict",
    [
        (
            "0, No | 1, Yes",
            {
                "type": "integer",
                "enumLabels": {"0": "No", "1": "Yes"},
                "constraints": {"enum": ["0", "1"]},
            },
        ),
        (
            "1," "Yes, one operation" "| 2," "Yes, more than one operation" "| 3, No",
            {
                "type": "integer",
                "enumLabels": {
                    "1": "Yes, one operation",
                    "2": "Yes, more than one operation",
                    "3": "No",
                },
                "constraints": {"enum": ["1", "2", "3"]},
            },
        ),
    ],
)
def test_parse_field_properties(test_encodings_string, expected_dict):
    """Test mapping function parse_field_properties_from_encodings"""
    assert (
        _parse_field_properties_from_encodings(test_encodings_string) == expected_dict
    )


@pytest.mark.parametrize(
    "input_dict, expected_output_dict",
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
def test_map_text(input_dict, expected_output_dict):
    """Test mapping function map_text"""
    assert map_text(input_dict) == expected_output_dict


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
        CHOICES_FIELD_NAME: "",
    }
    expected_message = (
        "Missing value in dropdown field '"
        f"{input_row.get('name')}"
        f"' in column '{CHOICES_LABEL_INPUT}'."
    )
    with pytest.raises(ValueError) as err:
        map_dropdown(input_row)
    assert expected_message in str(err.value)


def test_map_radio_with_error():
    """Test that map_radio raises error with empty Choices field"""
    input_row = {
        "name": "some_field_name",
        CHOICES_FIELD_NAME: "",
    }
    field_name = input_row.get("name")
    expected_message = (
        f"Missing radio values in 'Choices' column for row '{field_name}'"
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


# TODO: add rows with repeated keys and missing values.
def test_map_checkbox_with_error():
    """Test that map_checkbox raises error with empty Choices field"""
    input_dict = {
        "name": "gym",
        "type": "checkbox",
        "choice_calc_lbls": "",
    }
    field_name = input_dict.get("name")
    expected_message = (
        f"Missing checkbox values in 'Choices' column for row '{field_name}'"
    )
    with pytest.raises(ValueError) as err:
        map_checkbox(input_dict)
    assert expected_message in str(err.value)


@pytest.mark.parametrize(
    "input_dict, expected_output_dict",
    [
        (
            {
                "name": "default_range_0_labels",
                "text_valid_slider_num": "integer",
            },
            {
                "type": "integer",
                "constraints": {"minimum": 0, "maximum": 100},
            },
        ),
        (
            {
                "name": "default_range_2_labels",
                "text_valid_slider_num": "integer",
                "choice_calc_lbls": "Not Confident|Very Confident",
            },
            {
                "type": "integer",
                "constraints": {"minimum": 0, "maximum": 100},
                "enumLabels": {"0": "Not Confident", "50": "", "100": "Very Confident"},
            },
        ),
        (
            {
                "name": "default_range_3_labels",
                "text_valid_slider_num": "integer",
                "choice_calc_lbls": "Not Confident|Confident|Very Confident",
            },
            {
                "type": "integer",
                "constraints": {"minimum": 0, "maximum": 100},
                "enumLabels": {
                    "0": "Not Confident",
                    "50": "Confident",
                    "100": "Very Confident",
                },
            },
        ),
        (
            {
                "name": "custom_min_3_labels",
                "text_valid_slider_num": "integer",
                "text_valid_min": "20",
                "choice_calc_lbls": "Not Confident|Confident|Very Confident",
            },
            {
                "type": "integer",
                "constraints": {"minimum": 20, "maximum": 100},
                "enumLabels": {
                    "20": "Not Confident",
                    "60": "Confident",
                    "100": "Very Confident",
                },
            },
        ),
        (
            {
                "name": "custom_max_3_labels",
                "text_valid_slider_num": "integer",
                "text_valid_max": "80",
                "choice_calc_lbls": "Not Confident|Confident|Very Confident",
            },
            {
                "type": "integer",
                "constraints": {"minimum": 0, "maximum": 80},
                "enumLabels": {
                    "0": "Not Confident",
                    "40": "Confident",
                    "80": "Very Confident",
                },
            },
        ),
        (
            {
                "name": "custom_number_3_labels",
                "text_valid_slider_num": "number",
                "text_valid_min": "1.1",
                "text_valid_max": "3.5",
                "choice_calc_lbls": "Not Confident|Confident|Very Confident",
            },
            {
                "type": "number",
                "constraints": {"minimum": 1.1, "maximum": 3.5},
                "enumLabels": {
                    "1.1": "Not Confident",
                    "2.3": "Confident",
                    "3.5": "Very Confident",
                },
            },
        ),
    ],
)
def test_map_slider(input_dict, expected_output_dict):
    """Test mapping function map_slider"""
    assert map_slider(input_dict) == expected_output_dict


@pytest.mark.parametrize(
    "input_dict, expected_error_message",
    [
        (
            {
                "name": "invalid integer",
                "text_valid_slider_num": "integer",
                "text_valid_min": "1.1",
                "text_valid_max": "3.5",
            },
            "Skipping non-integer min value '1.1' for row 'invalid integer'",
        ),
        (
            {
                "name": "invalid number",
                "text_valid_slider_num": "number",
                "text_valid_min": "1.1",
                "text_valid_max": "foo",
            },
            "Skipping non-numeric max value 'foo' for row 'invalid number'",
        ),
    ],
)
def test_map_slider_with_error(input_dict, expected_error_message):
    """Test that map_slider raises error with invalid Text Min and Max"""
    with pytest.raises(ValueError) as err:
        map_slider(input_dict)
    assert expected_error_message in str(err.value)
