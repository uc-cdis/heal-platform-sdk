import json
from pathlib import Path
import pytest

from heal.vlmd.extract.utils import (
    embed_data_dictionary_props,
    parse_list_str,
    refactor_field_props,
    unflatten_from_jsonpath,
)

schema_version = {"schemaVersion": {"type": "string"}}
another_field_to_rearrange = {
    "anotherFieldToEmbed": {
        "items": {"type": "object", "properties": {"thisone": {"type": "string"}}}
    }
}
schema_to_rearrange = {
    "version": "0.2.0",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "test",
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        **schema_version,
        **another_field_to_rearrange,
        "anotherFieldToEmbed": {
            "items": {
                "type": "object",
                "properties": {"thisone": {"type": "string"}},
            }
        },
        "fields": {
            "type": "array",
            "items": {
                "properties": {
                    "type": "object",
                    "some_field": {"type": "string"},
                    **schema_version,
                    **another_field_to_rearrange,
                }
            },
        },
    },
}


def test_unflatten_jsonpath():
    input = {
        "module": "Testing",
        "constraints.enum": "1|2|3|4",
        "standardsMappings[1].item.url": "http//:helloitem1",
        "standardsMappings[0].item.url": "http//:helloitem0",
        "standardsMappings[0].instrument.url": "http//:helloworld0",
        "standardsMappings[1].instrument.url": "http//:helloworld1",
        "standardsMappings[2].item.url": "http//:helloitem2",
        "test1.test2.test3[1]": "test3_1",
        "test1.test2.test3[0].test4": "test4_1",
    }

    output = {
        "module": "Testing",
        "constraints": {"enum": "1|2|3|4"},
        "standardsMappings": [
            {
                "item": {"url": "http//:helloitem0"},
                "instrument": {"url": "http//:helloworld0"},
            },
            {
                "item": {"url": "http//:helloitem1"},
                "instrument": {"url": "http//:helloworld1"},
            },
            {"item": {"url": "http//:helloitem2"}},
        ],
        "test1": {"test2": {"test3": [{"test4": "test4_1"}, {"test3": "test3_1"}]}},
    }
    field_json = unflatten_from_jsonpath(input)
    assert (
        field_json == output
    ), "Problem with converting input dictionary to output dictionary"


def test_embed_data_dictionary_props():
    flat_root = {
        "schemaVersion": "0.2.0",
        "anotherFieldToEmbed[0].thisone": "helloworld",
    }
    flat_fields_array = [{"some_field": "cool"}, {"some_field": "sad"}]
    flat_fields = embed_data_dictionary_props(
        flat_fields_array, flat_root, schema_to_rearrange
    )

    assert flat_fields.to_dict(orient="records") == [
        {
            "some_field": "cool",
            "schemaVersion": "0.2.0",
            "anotherFieldToEmbed[0].thisone": "helloworld",
        },
        {
            "some_field": "sad",
            "schemaVersion": "0.2.0",
            "anotherFieldToEmbed[0].thisone": "helloworld",
        },
    ]


def test_refactor_field_props():
    flat_fields_array = [
        {"some_field": "cool", "anotherFieldToEmbed[0].thisone": "helloworld"},
        {"some_field": "sad", "anotherFieldToEmbed[0].thisone": "helloworld"},
    ]
    flat_root, flat_fields = refactor_field_props(
        flat_fields_array, schema_to_rearrange
    )

    assert flat_root.to_dict() == {"anotherFieldToEmbed[0].thisone": "helloworld"}
    assert flat_fields.to_dict(orient="records") == [
        {"some_field": "cool"},
        {"some_field": "sad"},
    ]


@pytest.mark.parametrize(
    "input_string, separator, expected_output_list",
    [
        ("a,b,c", ",", ["a", "b", "c"]),
        ("a|b|c", "|", ["a", "b", "c"]),
        ("a|b|c", "#", ["a|b|c"]),
    ],
)
def test_parse_list_str(input_string, separator, expected_output_list):
    result = parse_list_str(input_string, separator)
    assert result == expected_output_list
