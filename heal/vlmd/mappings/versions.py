"""
holds the mappings for previous schema version
field names (headers, properties) and the current name
in addition to these field name values or value mappings.

"""
from heal.vlmd.config import JSON_SCHEMA

VERSION = ["0", "3"]

root_mappings = [
    {"target": "fields", "source": ["data_dictionary"]},
    {"target": "schemaVersion", "source": [None], "value": JSON_SCHEMA["version"]},
]


field_mappings = [
    {
        "target": "schemaVersion",
        "source": [None],
        # should be same as csv schema version
        "values": JSON_SCHEMA["version"],
    },
    {"target": "section", "source": ["module"]},
    {"target": "enumLabels", "source": ["encoding", "encodings"]},
    {"target": "enumOrdered", "source": ["ordered"]},
    {
        "target": "standardsMappings[0].instrument.source",
        "source": ["standardsMappings.type", "standardsMappings[0].source"],
    },
    {
        "target": "standardsMappings[0].instrument.title",
        "source": ["standardsMappings.label", "standardsMappings[0].title"],
    },
    {
        "target": "standardsMappings[0].item.source",
        "source": ["standardsMappings.source", "standardsMappings[0].source"],
    },
    {
        "target": "standardsMappings[0].item.id",
        "source": ["standardsMappings.id", "standardsMappings[0].id"],
    },
    {
        "target": "standardsMappings[0].item.url",
        "source": ["standardsMappings.url", "standardsMappings[0].url"],
    },
    {
        "target": None,
        "source": ["repo_link"],
    },
    {
        "target": None,
        "source": [
            "relatedConcepts.type",
            "relatedConcepts.label",
            "relatedConcepts.url",
            "relatedConcepts.source",
            "relatedConcepts.id",
            "relatedConcepts",
        ],
    },
    {
        "target": None,
        "source": [
            "univarStats.median",
            "univarStats.mean",
            "univarStats.std",
            "univarStats.min",
            "univarStats.max",
            "univarStats.mode",
            "univarStats.count",
            "univarStats.twentyFifthPercentile",
            "univarStats.seventyFifthPercentile",
            "univarStats.categoricalMarginals.name",
            "univarStats.categoricalMarginals.count",
        ],
    },
]


root_rename_map = {
    source_name: item["target"]
    for item in root_mappings
    for source_name in item["source"]
    if item["target"] and source_name
}
root_addmap = {"schemaVersion": JSON_SCHEMA["version"]}
fields_recode_map = {}
fields_rename_map = {
    source_name: item["target"]
    for item in field_mappings
    for source_name in item["source"]
    if item["target"] and source_name
}
fields_drop_list = [
    source_name
    for item in field_mappings
    for source_name in item["source"]
    if not item["target"] and source_name
]
fields_addmap = {"schemaVersion": JSON_SCHEMA["version"]}
