import json
from pathlib import Path

# file prefix
OUTPUT_FILE_PREFIX = "heal-dd"

# file suffixes
ALLOWED_INPUT_TYPES = ["csv", "tsv", "json"]
ALLOWED_FILE_TYPES = ["auto", "csv", "tsv", "json", "redcap"]
ALLOWED_SCHEMA_TYPES = ["auto", "csv", "json", "tsv"]
ALLOWED_OUTPUT_TYPES = ["csv", "json"]

# schemas
schema_dir_path = Path(__file__).parents[1].joinpath("vlmd/schemas")

csv_schema_path = schema_dir_path.joinpath("heal_csv.json")
with open(csv_schema_path, "r") as schema_file:
    CSV_SCHEMA = json.load(schema_file)

json_schema_path = schema_dir_path.joinpath("heal_json.json")
with open(json_schema_path, "r") as schema_file:
    JSON_SCHEMA = json.load(schema_file)

# schema
JSON_SCHEMA_VERSION = JSON_SCHEMA.get("version", "0.3.2")
# The title is a default title used in the validation process.
# It will get overwritten by a user-specified title in the extraction process.
TOP_LEVEL_PROPS = {
    "schemaVersion": JSON_SCHEMA_VERSION,
    "title": "HEAL Data Dictionary",
}
