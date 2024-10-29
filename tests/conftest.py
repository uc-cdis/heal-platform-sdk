import pytest

from heal.vlmd.config import (
    ALLOWED_INPUT_TYPES,
    ALLOWED_SCHEMA_TYPES,
    CSV_SCHEMA,
    JSON_SCHEMA,
)


@pytest.fixture()
def VALID_CSV_SCHEMA():
    return CSV_SCHEMA


@pytest.fixture()
def VALID_JSON_SCHEMA():
    return JSON_SCHEMA


@pytest.fixture()
def allowed_input_types():
    return ALLOWED_INPUT_TYPES


@pytest.fixture()
def allowed_schema_types():
    return ALLOWED_SCHEMA_TYPES


@pytest.fixture()
def invalid_csv_schema():
    # type=5 is not of type 'object', 'boolean'
    return {
        "type": "array",
        "items": {
            "version": "0.3.2",
            "properties": {
                "title": 5,
                "items": {
                    "foo": "bar",
                },
            },
        },
    }


@pytest.fixture()
def invalid_json_schema():
    # type=5 is not of type 'object', 'boolean'
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Variable Level Metadata (Data Dictionaries)",
        "type": "object",
        "required": ["title", "fields"],
        "properties": {
            "title": 5,
            "version": {
                "type": "string",
                "description": "The version",
            },
        },
    }


@pytest.fixture()
def valid_array_data():
    return [
        {
            "section": "Enrollment",
            "name": "participant_id",
            "title": "Participant Id",
            "description": "Unique identifier for participant",
            "type": "string",
            "format": "",
            "constraints.maxLength": "",
            "constraints.enum": "",
            "constraints.pattern": "[A-Z][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
            "constraints.maximum": "",
            "constraints.minimum": "",
            "enumLabels": "",
            "enumOrdered": "",
            "missingValues": "",
            "trueValues": "",
            "falseValues": "",
            "custom.notes": "This is a note",
        },
        {
            "section": "Demographics",
            "name": "race",
            "title": "Race",
            "description": "Self-reported race",
            "type": "integer",
            "format": "",
            "constraints.maxLength": "",
            "constraints.enum": "1|2|3|4|5|6|7|8",
            "constraints.pattern": "",
            "constraints.maximum": "",
            "constraints.minimum": "",
            "enumLabels": "1=White|2=Black or African American|3=American Indian or Alaska Native|4=Native| 5=Hawaiian or Other Pacific Islander|6=Asian|7=Some other race|8=Multiracial|99=Not reported",
            "enumOrdered": "",
            "missingValues": "99",
            "trueValues": "",
            "falseValues": "",
            "custom.notes": "This is a custom note",
        },
    ]
