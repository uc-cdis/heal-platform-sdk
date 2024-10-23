import json

ALLOWED_INPUT_TYPES = ["csv", "tsv", "json"]
ALLOWED_SCHEMA_TYPES = ["auto", "csv", "json", "tsv"]

csv_schema_file = "heal/vlmd/schemas/heal_csv.json"
with open(csv_schema_file, "r") as f:
    CSV_SCHEMA = json.load(f)

json_schema_file = "heal/vlmd/schemas/heal_json.json"
with open(json_schema_file, "r") as f:
    JSON_SCHEMA = json.load(f)
