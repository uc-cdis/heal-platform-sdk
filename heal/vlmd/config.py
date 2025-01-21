import json

# file prefix
OUTPUT_FILE_PREFIX = "heal-dd"

# file suffixes
ALLOWED_INPUT_TYPES = ["csv", "tsv", "json"]
ALLOWED_FILE_TYPES = ["auto"] + ALLOWED_INPUT_TYPES
ALLOWED_SCHEMA_TYPES = ["auto", "csv", "json", "tsv"]
ALLOWED_OUTPUT_TYPES = ["csv", "json"]

# schemas
csv_schema_file = "heal/vlmd/schemas/heal_csv.json"
with open(csv_schema_file, "r") as f:
    CSV_SCHEMA = json.load(f)

json_schema_file = "heal/vlmd/schemas/heal_json.json"
with open(json_schema_file, "r") as f:
    JSON_SCHEMA = json.load(f)

# schema
JSON_SCHEMA_VERSION = JSON_SCHEMA.get("version", "0.3.2")
TOP_LEVEL_PROPS = {
    "schemaVersion": JSON_SCHEMA_VERSION,
    "title": "HEAL Data Dictionary",
}
