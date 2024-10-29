def add_missing_type(prop_name: str, prop, schema: dict):
    """
    Add types to properties.

    Args:
        prop_name (str): property name
        prop (str or dict): property
        schema (dict): schema

    Returns:
        schema (dict)

    """
    missing_values = ["", None]  # NOTE: include physical rep and logical for now
    if prop_name in schema.get("required", []):
        # if required value: MUST be NOT missing value and the property
        newprop = {"allOf": [prop, {"not": {"enum": missing_values}}]}
    else:
        # if not required value: MUST be property OR the specified missing value
        newprop = {"anyOf": [prop, {"enum": missing_values}]}
    return newprop


def add_types_to_props(schema: dict) -> dict:
    """
    Add missing types to the schema for validating csv style data.

    Args:
        schema (dict)

    Returns:
        schema (dict)
    """

    props_with_missing = {}
    for prop_name, prop in schema.get("items", {}).get("properties", {}).items():
        props_with_missing[prop_name] = add_missing_type(prop_name, prop, schema)

    patterns_with_missing = {}
    for pattern_name, prop in (
        schema.get("items", {}).get("patternProperties", {}).items()
    ):
        patterns_with_missing[pattern_name] = add_missing_type(
            pattern_name, prop, schema
        )

    schema = {"type": "array", "items": {}}
    schema["items"]["properties"] = props_with_missing
    schema["items"]["patternProperties"] = patterns_with_missing

    return schema


def remove_empty_props(props):
    """
    Remove any fields with emtpy values.
    Can be used for json dictionaries that have been extracted from csv dictionaries.
    """
    if isinstance(props, dict):
        new_dict = {}
        for k, v in props.items():
            cleaned_value = remove_empty_props(v)
            if cleaned_value or cleaned_value == 0:
                new_dict[k] = cleaned_value
        return new_dict
    return props