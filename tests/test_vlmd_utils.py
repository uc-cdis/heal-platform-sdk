import pytest

from heal.vlmd.utils import (
    add_missing_type,
    add_types_to_props,
    remove_empty_props,
)


def test_add_missing_type():
    # Required prop_name gets "allOf" in prop value
    prop_name = "description"
    prop_value = "Some string value"
    schema = {"required": ["description"]}
    expected_new_prop = {"allOf": [prop_value, {"not": {"enum": ["", None]}}]}

    new_prop = add_missing_type(prop_name, prop_value, schema)
    assert new_prop == expected_new_prop

    # Non-required prop_name gets "anyOf" in prop value
    prop_name = "name of non-required prop"
    expected_new_prop = {"anyOf": [prop_value, {"enum": ["", None]}]}

    new_prop = add_missing_type(prop_name, prop_value, schema)
    assert new_prop == expected_new_prop


@pytest.mark.parametrize(
    "input_schema,expected_schema",
    [
        (
            {"type": "array", "comment": "empty items", "items": {}},
            {"type": "array", "items": {"properties": {}, "patternProperties": {}}},
        ),
        (
            {
                "type": "array",
                "comment": "required field: 'description'",
                "items": {
                    "version": "0.3.2",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
                "required": ["description"],
            },
            {
                "type": "array",
                "items": {
                    "properties": {
                        "title": {"anyOf": [{"type": "string"}, {"enum": ["", None]}]},
                        "description": {
                            "allOf": [{"type": "string"}, {"not": {"enum": ["", None]}}]
                        },
                    },
                    "patternProperties": {},
                },
            },
        ),
        (
            {
                "type": "array",
                "comment": "includes 'patternProperties'",
                "items": {
                    "version": "0.3.2",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "items": {
                            "foo": "bar",
                        },
                    },
                    "patternProperties": {
                        "^standardsMappings\\[\\d+\\].instrument.url$": {
                            "title": "Url",
                            "description": "A url",
                        },
                    },
                },
                "required": ["description"],
            },
            {
                "type": "array",
                "items": {
                    "properties": {
                        "title": {"anyOf": [{"type": "string"}, {"enum": ["", None]}]},
                        "description": {
                            "allOf": [{"type": "string"}, {"not": {"enum": ["", None]}}]
                        },
                        "items": {"anyOf": [{"foo": "bar"}, {"enum": ["", None]}]},
                    },
                    "patternProperties": {
                        "^standardsMappings\\[\\d+\\].instrument.url$": {
                            "anyOf": [
                                {"title": "Url", "description": "A url"},
                                {"enum": ["", None]},
                            ]
                        }
                    },
                },
            },
        ),
    ],
)
def test_add_types_to_props(input_schema, expected_schema):
    # Propeties get wrapped in 'anyOf' or 'allOf'
    result = add_types_to_props(input_schema)
    assert result == expected_schema


def test_remove_empty_props():
    input_prop = {
        "section": "Enrollment",
        "name": "participant_id",
        "title": "Participant Id",
        "description": "Unique identifier for participant",
        "type": "string",
        "format": "",
        "constraints": {
            "maxLength": 5,
            "enum": "",
            "pattern": "[A-Z][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
            "maximum": 10.0,
            "minimum": "",
        },
        "empty_constraints": {"maxLength": ""},
        "empty_enum": [],
        "missingValues": "",
        "trueValues": "",
        "falseValues": "",
    }
    expected_prop = {
        "section": "Enrollment",
        "name": "participant_id",
        "title": "Participant Id",
        "description": "Unique identifier for participant",
        "type": "string",
        "constraints": {
            "maxLength": 5,
            "pattern": "[A-Z][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
            "maximum": 10.0,
        },
    }

    result = remove_empty_props(input_prop)
    assert result == expected_prop
