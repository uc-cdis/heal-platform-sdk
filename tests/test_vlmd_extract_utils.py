import json
from pathlib import Path
from jsonschema import ValidationError
import pytest

from heal.vlmd.extract.utils import (
    _get_prop_names_to_rearrange,
    embed_data_dictionary_props,
    find_prop_name,
    flatten_properties,
    flatten_to_json_path,
    join_dict_items,
    parse_dictionary_str,
    parse_list_str,
    refactor_field_props,
    unflatten_from_json_path,
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


def test_unflatten_from_json_path():
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
    field_json = unflatten_from_json_path(input)
    assert (
        field_json == output
    ), "Problem with converting input dictionary to output dictionary"


@pytest.mark.parametrize(
    "invalid_input, invalid_name",
    [
        (
            {
                "module": "Testing",
                "constraints.enum": "1|2|3|4",
                "standardsMappings[1].item.url": "http//:helloitem1",
                "standardsMappings['some_string'].item.url": "http//:helloitem0",
                "standardsMappings[2].item.url": "http//:helloitem2",
            },
            "standardsMappings['some_string']",
        ),
        (
            {
                "module": "Testing",
                "constraints.enum": "1|2|3|4",
                "[1].item.url": "http//:helloitem1",
                "standardsMappings[0].item.url": "http//:helloitem0",
                "standardsMappings[2].item.url": "http//:helloitem2",
            },
            "[1]",
        ),
        (
            {
                "module": "Testing",
                "constraints.enum": "1|2|3|4",
                "standardsMappings[1).item.url": "http//:helloitem1",
                "standardsMappings[0].item.url": "http//:helloitem0",
                "standardsMappings[2].item.url": "http//:helloitem2",
            },
            "standardsMappings[1)",
        ),
    ],
)
def test_unflatten_from_json_path_invalid_input(invalid_input, invalid_name):
    with pytest.raises(ValidationError) as e:
        unflatten_from_json_path(invalid_input)
    expected_error_message = f"Incorrect array indexing in name {invalid_name}"
    assert expected_error_message in str(e.value)


def test_get_prop_names_to_rearrange():
    flat_root = {
        "schemaVersion": "0.2.0",
        "title": "Example VLMD",
        "description": "This is an example description",
        "anotherFieldToEmbed[0].thisone": "helloworld",
    }
    prop_names = list(flat_root.keys())
    expected_prop_names = ["schemaVersion", "anotherFieldToEmbed[0].thisone"]
    names_to_rearrange = _get_prop_names_to_rearrange(prop_names, schema_to_rearrange)
    assert names_to_rearrange == expected_prop_names


def test_flatten_to_json_path(valid_json_data, VALID_JSON_SCHEMA):
    # example field item
    dict_field = {
        "section": "Enrollment",
        "name": "participant_id",
        "constraints": {"pattern": "[A-Z][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]"},
    }
    expected_flattened_dict = {
        "section": "Enrollment",
        "name": "participant_id",
        "constraints.pattern": "[A-Z][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
    }
    fields_schema = VALID_JSON_SCHEMA["properties"]["fields"]["items"]
    flattened_dict = flatten_to_json_path(dict_field, fields_schema)
    assert flattened_dict == expected_flattened_dict


def test_flatten_properties():
    schema_props = schema_to_rearrange["properties"]
    expected_props = {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "schemaVersion": {"type": "string"},
        "anotherFieldToEmbed\\[\\d+\\].thisone": {"type": "string"},
        "fields\\[\\d+\\].type": "object",
        "fields\\[\\d+\\].some_field": {"type": "string"},
        "fields\\[\\d+\\].schemaVersion": {"type": "string"},
        "fields\\[\\d+\\].anotherFieldToEmbed\\[\\d+\\].thisone": {"type": "string"},
    }
    assert flatten_properties(schema_props) == expected_props


@pytest.mark.parametrize(
    "name, field_props, expected_name",
    [
        (
            "foo",
            {
                "title": "HEAL Variable Level Metadata Fields",
                "description": "Some description",
                "foo": "bar",
            },
            "foo",
        ),
        (
            "foo",
            {
                "title": "HEAL Variable Level Metadata Fields",
                "description": "Some description",
                "bar": "foo",
            },
            None,
        ),
        (
            "foo",
            {
                "title": "HEAL Variable Level Metadata Fields",
                "description": "Some description",
                "barfoo": "bar",
            },
            None,
        ),
    ],
)
def test_find_prop_names(name, field_props, expected_name):
    assert find_prop_name(name, field_props) == expected_name


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


def test_parse_dictionary_str():
    input_string = "title=Example VLMD|description=This is an example description|fields=[{'section': 'Enrollment', 'name': 'participant_id'}]"
    expected_dict = {
        "title": "Example VLMD",
        "description": "This is an example description",
        "fields": "[{'section': 'Enrollment', 'name': 'participant_id'}]",
    }
    output_dict = parse_dictionary_str(input_string, item_sep="|", key_val_sep="=")
    assert output_dict == expected_dict


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


def test_join_dict_items():
    dict = {
        "title": "Example VLMD",
        "description": "This is an example description",
        "fields": [
            {
                "section": "Enrollment",
                "name": "participant_id",
            },
        ],
    }
    expected = "title=Example VLMD|description=This is an example description|fields=[{'section': 'Enrollment', 'name': 'participant_id'}]"
    assert join_dict_items(dict) == expected
