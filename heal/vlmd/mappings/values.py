"""
defines potential source (input) values for the specified field property
that should map directly onto the target (the heal specification) without
any ambiguity
"""

from heal.vlmd.config import CSV_SCHEMA


def _flatten(map):
    return {sourcename: item["target"] for item in map for sourcename in item["source"]}


type_map = [
    {"target": "integer", "source": ["int"]},
    {
        "target": "string",
        "source": [
            "str",
            "character",
            "char",
            "text",
            "varchar",
            "alphanumeric",
            "alphanum",
        ],
    },
    {"target": "number", "source": ["num", "float", "decimal", "numeric"]},
    {"target": "boolean", "source": ["bool"]},
]
required_map = [
    {"target": True, "source": ["true", "1", "yes", "y", "required"]},
    {"target": False, "source": ["false", "0", "no", "not required", "n"]},
]
recode_map = {
    "type": _flatten(type_map),
    "constraints.required": _flatten(required_map),
}


def slugify(value: str) -> str:
    """
    Normalise a csv header or value before it is looked up in the rename or
    recode maps, e.g. " Data_Type " -> "data-type".
    """
    return value.strip().lower().replace("_", "-").replace(" ", "-")


def check_type_aliases(type_aliases: dict):
    """
    Raise ValueError if any target in a {source: target} type alias map is not
    a type allowed by the csv schema.
    """
    allowed_types = CSV_SCHEMA["properties"]["type"]["enum"]
    invalid = {
        source: target
        for source, target in type_aliases.items()
        if target not in allowed_types
    }
    if invalid:
        raise ValueError(
            f"Cannot map types {invalid}: targets must be one of {allowed_types}"
        )


def add_type_aliases(base_recode_map: dict, type_aliases: dict) -> dict:
    """
    Return a copy of a recode map with extra `type` aliases, e.g.
    {"Whole Number": "integer"}. Keys are slugified like the values they are
    matched against, and override the aliases already in the map.
    """
    check_type_aliases(type_aliases)
    return {
        **base_recode_map,
        "type": {
            **base_recode_map.get("type", {}),
            **{slugify(source): target for source, target in type_aliases.items()},
        },
    }
