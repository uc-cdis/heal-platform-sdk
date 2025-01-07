"""
defines potential source (input) values for the specified field property
that should map directly onto the target (the heal specification) without
any ambiguity
"""


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
