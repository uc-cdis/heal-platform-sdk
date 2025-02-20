"""
Functions for each REDCap field type that uses REDCap field info to determine
various pieces of field metadata.

Input assumes a dictionary with {"REDCap field_name": "REDCap value"}

REDCap dictionary fields:

NOTES - large text box for lots of text
DROPDOWN - dropdown menu with options
RADIO - radio buttons with options
CHECKBOX - checkboxes to allow selection of more than one option
FILE - upload a document
CALC - perform real-time calculations
SQL - select query statement to populate dropdown choices
DESCRIPTIVE - text displayed with no data entry and optional image/file attachment
SLIDER - visual analogue scale; coded as 0-100
YESNO - radio buttons with yes and no options; coded as 1, Yes | 0, No
TRUEFALSE - radio buttons with true and false options; coded as 1, True | 0, False
"""

import re

from cdislogging import get_logger

from heal.vlmd.extract import utils
from heal.vlmd.mappings.redcap_csv_headers import (
    CALC_FIELD_NAME,
    CHOICES_FIELD_NAME,
    CHOICES_LABEL_INPUT,
    SLIDER_FIELD_NAME,
    TEXT_VALID_FIELD_NAME,
)

logger = get_logger("redcap-mapping", log_level="warning")


def _parse_field_properties_from_encodings(encodings_string: str) -> dict:
    """
    Many of the field types have the same logic
    for conversion to data types and just differ
    in presentation (dropbox, radio box) so making
    fxn to support this

    Currently supports strings, ints, and nums for types
    """
    # parse encodings
    field_encodings = utils.parse_dictionary_str(
        encodings_string, item_sep="|", key_val_sep=","
    )
    # get enums
    field_enums = list(field_encodings.keys())
    # interpret type from enums
    for value in field_enums:
        value = value.strip()
        if value.isnumeric():
            try:
                int(value)
                field_type = "integer"
            except ValueError:
                field_type = "number"
        else:
            field_type = "string"

    return {
        "type": field_type,
        "enumLabels": {
            key.strip(): value.strip() for key, value in field_encodings.items()
        },
        "constraints": {"enum": [value.strip() for value in field_enums]},
    }


def map_text(field: dict) -> dict:
    """
    TEXT - single-line text box (for text and numbers)

    Looks at the text validation field, defined by
    'TEXT_VALID_FIELD_NAME' in 'redcap_csv_headers.py'
    """
    integer_pattern = r"^-?\s*\d+\s*$"
    number_pattern = r"^-?\s*\d+(\.\d+)?([eE][-+]?\d+)?\s*$"
    if field.get(TEXT_VALID_FIELD_NAME):
        text_validation = field[TEXT_VALID_FIELD_NAME].lower()
    else:
        text_validation = ""
    field_format = None
    field_pattern = None
    constraints_min = None
    constraints_max = None
    if "datetime" in text_validation:
        field_type = "datetime"
        field_format = "any"
    elif "date" in text_validation:
        field_type = "date"
        field_format = "any"
    elif text_validation == "email":
        field_type = "string"
        field_format = "email"
    elif text_validation == "integer":
        field_type = "integer"
        min_value = field.get("text_valid_min")
        if min_value:
            if re.match(integer_pattern, min_value):
                constraints_min = int(min_value)
            else:
                warning_message = (
                    f"Skipping conversion of min value '{min_value}' for field '"
                    f"{field.get('name')}"
                    "'"
                )
                logger.warning(warning_message)
        max_value = field.get("text_valid_max")
        if max_value:
            if re.match(integer_pattern, max_value):
                constraints_max = int(max_value)
            else:
                warning_message = (
                    f"Skipping conversion of max value '{max_value}' for field '"
                    f"{field.get('name')}"
                    "'"
                )
                logger.warning(warning_message)
    elif text_validation == "alpha_only":
        field_type = "string"
        field_pattern = "^[a-zA-Z]+$"
    elif "number" in text_validation:
        field_type = "number"
        min_value = field.get("text_valid_min")
        if min_value:
            if "comma_decimal" in text_validation:
                min_value.replace(",", ".")
            if re.match(number_pattern, min_value):
                constraints_min = float(min_value)
            else:
                warning_message = (
                    f"Skipping conversion of min value '{min_value}' for field '"
                    f"{field.get('name')}"
                    "'"
                )
                logger.warning(warning_message)
        max_value = field.get("text_valid_max")
        if max_value:
            if "comma_decimal" in text_validation:
                max_value = max_value.replace(",", ".")
            if re.match(number_pattern, max_value):
                constraints_max = float(max_value)
            else:
                warning_message = (
                    f"Skipping conversion of max value '{max_value}' for field '"
                    f"{field.get('name')}"
                    "'"
                )
                logger.warning(warning_message)
    elif text_validation == "phone":
        field_type = "string"
        field_pattern = "^[0-9]{3}-[0-9]{3}-[0-9]{4}$"
    elif text_validation == "postalcode_australia":
        field_type = "string"
        field_pattern = "^[0-9]{4}$"
    elif text_validation == "postalcode_canada":
        field_type = "string"
        field_pattern = "^[A-Z][0-9][A-Z] [0-9][A-Z][0-9]$"
    elif text_validation == "ssn":
        field_type = "string"
        field_pattern = "^[0-9]{3}-[0-9]{2}-[0-9]{4}$"
    elif "time" in text_validation:
        field_type = "time"
        field_format = "any"
    elif text_validation == "vmrn":
        field_type = "string"
        field_pattern = "^[0-9]{10}$"
    elif text_validation == "zipcode":
        field_type = "string"
        field_pattern = "^[0-9]{5}$"
    else:
        field_type = "string"

    props = dict(
        zip(
            ["type", "format", "constraints"],
            [
                field_type,
                field_format,
                {
                    "pattern": field_pattern,
                    "minimum": constraints_min,
                    "maximum": constraints_max,
                },
            ],
        )
    )

    # delete props without values (ie None)
    for prop_name in ["type", "format"]:
        if props[prop_name] is None:
            del props[prop_name]
    # constraints will be cleaned later

    return props


def map_notes(field: dict) -> dict:
    """
    NOTES - large text box for lots of text
    """
    return {"type": "string"}


def map_dropdown(field: dict) -> dict:
    """
    DROPDOWN - dropdown menu with options

    Determined by "options" (ie Choices, Calculations, OR Slider Labels)
    """
    encodings_string = field[CHOICES_FIELD_NAME]
    if not encodings_string:
        error_message = (
            "Missing value in dropdown field '"
            f"{field.get('name')}"
            f"' in column '{CHOICES_LABEL_INPUT}'."
        )
        raise ValueError(error_message)
    return _parse_field_properties_from_encodings(encodings_string)


def map_radio(field: dict) -> dict:
    """
    RADIO - radio buttons with options

    Determined by "options" (ie Choices, Calculations, OR Slider Labels)
    """
    encodings_string = field[CHOICES_FIELD_NAME]
    if not encodings_string:
        error_message = (
            "Missing value in radio field '"
            f"{field.get('name')}"
            f"' in column '{CHOICES_LABEL_INPUT}'."
        )
        raise ValueError(error_message)
    return _parse_field_properties_from_encodings(encodings_string)


def map_checkbox(field: dict) -> dict:
    """
    CHECKBOX	- checkboxes to allow selection of more than one option

    ## Are data from checkbox (choose all that apply) field types handled
    differently from other field types when imported or exported?
    Yes. When your data are exported, each option from a checkbox field
    becomes a separate variable coded 1 or 0 to reflect whether it is checked
    or unchecked. By default, each option is pre-coded 0, so even if you have
    not yet collected any data, you will see 0's for each checkbox option.
    The variable names will be the name of the field followed by the option number.
    So, for example, if you have a field coded as follows:

    Race

    1, Caucasian
    2, African American
    3, Asian
    4, Other

    In your exported dataset, you will have four variables representing the field
    Race that will be set as 0 by default, coded 1 if the option was checked for
    a record. The variable names will consist of the field name, three underscores,
    and the choice value:

    race___1
    race___2
    race___3
    race___4

    Notes:

    when you import data into a checkbox field, you must code it based on the same model
    negative values can be used as the raw coded values for checkbox fields. Due to certain
    limitations, negative values will not work when importing values using the
    Data Import Tool, API and cause problems when exporting data into a statistical
    analysis package. The workaround is that negative signs are replaced by an underscore
    in the export/import-specific version of the variable name (e.g., for a checkbox
    named "race", its choices "2" and "-2" would export as the fields

    race___2
    race____2

    A checkbox field can be thought of as a series of yes/no questions in one field.
    Therefore, a yes (check) is coded as 1 and a no (uncheck) is coded a 0.
    An unchecked response on a checkbox field is still regarded as an answer and
    is not considered missing.
    """
    checkbox_name = field["name"]
    choices = utils.parse_dictionary_str(
        field[CHOICES_FIELD_NAME], item_sep="|", key_val_sep=","
    )
    field_type = "boolean"
    field_enums = ["0", "1"]
    field_encodings = {"0": "Unchecked", "1": "Checked"}

    fields_new = [
        {
            "description": f"[choice={choice}]",
            "title": checkbox_name.title() + ": " + choice,
            "name": checkbox_name
            + "___"
            + re.sub(
                "^\-", "_", val
            ).strip(),  # NOTE: REDCAP changes negative sign to underscore
            "type": field_type,
            "constraints": {"enum": field_enums},
            "enumLabels": field_encodings,
        }
        for val, choice in choices.items()
    ]
    return fields_new


def map_file(field: dict) -> dict:
    return {"type": "string"}


def map_calc(field: dict) -> dict:
    return {"description": f"[calculation: {field[CALC_FIELD_NAME]}]", "type": "number"}


def map_sql(field: dict):
    return None


def map_yes_no(field: dict) -> dict:
    return {
        "type": "boolean",
        "constraints": {"enum": ["0", "1"]},
        "enumLabels": {"0": "No", "1": "Yes"},
    }


def map_true_false(field: dict) -> dict:
    return {
        "type": "boolean",
        "constraints": {"enum": ["0", "1"]},
        "enumLabels": {"0": "False", "1": "True"},
    }


def map_slider(field: dict) -> dict:
    vallist = ["0", "50", "100"]
    lbllist = utils.parse_list_str(field[SLIDER_FIELD_NAME], "|")
    field_encodings = {vallist[i]: lbl for i, lbl in enumerate(lbllist)}
    return {
        "type": "integer",
        "constraints": {"minimum": 0, "maximum": 100},
        "enumLabels": field_encodings,
    }


def map_descriptive(field: dict):
    return None


# not mapping descriptives or sql (TODO: mapping sql?)
type_mappings = {
    "text": map_text,
    "notes": map_notes,
    "dropdown": map_dropdown,
    "radio": map_radio,
    "checkbox": map_checkbox,
    "slider": map_slider,
    "yesno": map_yes_no,
    "truefalse": map_true_false,
    "calc": map_calc,
    "file": map_file,
}
