condensed_renamemap = {
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

renamemap = {
    source: target
    for target, sourcelist in condensed_renamemap.items()
    for source in sourcelist
}
