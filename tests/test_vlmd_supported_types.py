import csv
import importlib.util
import io
from pathlib import Path

from heal.vlmd.config import CSV_SCHEMA
from heal.vlmd.mappings import recode_map
from heal.vlmd.mappings.redcap_field_mapping import type_mappings

REPO_ROOT = Path(__file__).parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "vlmd_supported_types.py"
COMMITTED_CSV = REPO_ROOT / "docs" / "vlmd_supported_types.csv"

spec = importlib.util.spec_from_file_location("vlmd_supported_types", SCRIPT_PATH)
vlmd_supported_types = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vlmd_supported_types)


def test_every_schema_type_has_one_row():
    rows = vlmd_supported_types.build_rows()
    assert [row["type"] for row in rows] == CSV_SCHEMA["properties"]["type"]["enum"]
    for row in rows:
        assert row["description"], f"no description parsed for '{row['type']}'"


def test_every_alias_is_listed():
    rows = {row["type"]: row for row in vlmd_supported_types.build_rows()}
    for alias, vlmd_type in recode_map["type"].items():
        assert alias in rows[vlmd_type]["accepted_aliases"].split("|")


def test_every_redcap_field_type_is_listed():
    sources = "|".join(
        row["redcap_sources"] for row in vlmd_supported_types.build_rows()
    )
    for field_type in type_mappings:
        assert field_type in sources


def test_committed_csv_is_up_to_date():
    expected = vlmd_supported_types.to_csv(vlmd_supported_types.build_rows())
    assert COMMITTED_CSV.read_text() == expected, (
        f"{COMMITTED_CSV} is out of date; regenerate it with "
        "'poetry run python scripts/vlmd_supported_types.py "
        "-o docs/vlmd_supported_types.csv'"
    )


def test_committed_csv_parses():
    rows = list(csv.DictReader(io.StringIO(COMMITTED_CSV.read_text())))
    assert list(rows[0].keys()) == vlmd_supported_types.COLUMNS
