from heal.vlmd.schemas.heal_csv import heal_csv_schema
from heal.vlmd.schemas.heal_json import heal_json_schema

ALLOWED_INPUT_TYPES = ["csv", "tsv", "json"]
ALLOWED_SCHEMA_TYPES = ["auto", "csv", "json", "tsv"]
CSV_SCHEMA = heal_csv_schema
JSON_SCHEMA = heal_json_schema
