condensed_rename_map = {
    "type": [
        "data-type",
        "data-types",
        "field-type",
        "field-types",
        "types",
        "variable-types",
        "variable-type",
    ],
    "name": [
        "variable-name",
        "variable-names",
        "column-name",
        "column-names",
        "field-name",
        "field-names",
    ],
    "title": [
        "variable-title",
        "variable-titles",
        "field-title",
        "field-titles",
        "field-label",
        "field-labels",
        "variable-label",
        "variable-labels",
    ],
    "description": [
        "definition",
        "definitions",
    ],
    "enumLabels": [
        "pv-description",
        "permissible-value-description",
        "variable-value-labels",
        "value-labels",
    ],
    "constraints.enum": [
        "admissible-values",
        "permissible-values",
        "possible-values",
        "enum",
        "enumerated-values",
        "valid-values",
    ],
}

rename_map = {
    source: target
    for target, source_list in condensed_rename_map.items()
    for source in source_list
}
