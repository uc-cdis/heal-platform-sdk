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
