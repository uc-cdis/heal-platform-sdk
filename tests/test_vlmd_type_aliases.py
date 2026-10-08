import pandas as pd
import pytest
from jsonschema import ValidationError

from heal.vlmd import ExtractionError, vlmd_extract, vlmd_validate
from heal.vlmd.extract.conversion import convert_to_vlmd
from heal.vlmd.mappings import recode_map
from heal.vlmd.mappings.values import add_type_aliases, check_type_aliases

CUSTOM_TYPES_CSV = "tests/test_data/vlmd/invalid/vlmd_custom_types.csv"
CUSTOM_TYPE_ALIASES = {
    "Whole Number": "integer",
    "calendar-date": "date",
    "free_text": "string",
}


def test_add_type_aliases_slugifies_keys():
    recoded = add_type_aliases(recode_map, {" Whole_Number ": "integer"})
    assert recoded["type"]["whole-number"] == "integer"
    # built-in aliases and other columns are kept
    assert recoded["type"]["int"] == "integer"
    assert recoded["constraints.required"] == recode_map["constraints.required"]


def test_add_type_aliases_overrides_built_in_aliases():
    recoded = add_type_aliases(recode_map, {"text": "any"})
    assert recoded["type"]["text"] == "any"
    # the shared recode_map is not modified
    assert recode_map["type"]["text"] == "string"


def test_check_type_aliases_rejects_unknown_target():
    with pytest.raises(ValueError, match="Cannot map types {'Whole Number': 'int'}"):
        check_type_aliases({"Whole Number": "int"})


def test_convert_csv_with_type_aliases():
    package = convert_to_vlmd(
        CUSTOM_TYPES_CSV,
        input_type="csv-data-dict",
        type_aliases=CUSTOM_TYPE_ALIASES,
    )
    fields = package["template_csv"]["fields"]
    assert [field["type"] for field in fields] == [
        "integer",
        "date",
        "string",
        "number",
    ]
    # only the type column is recoded
    assert fields[0]["description"] == "Age in years as a Whole Number"


def test_validate_with_type_aliases():
    with pytest.raises(ValidationError):
        vlmd_validate(CUSTOM_TYPES_CSV, file_type="csv")
    assert vlmd_validate(
        CUSTOM_TYPES_CSV, file_type="csv", type_aliases=CUSTOM_TYPE_ALIASES
    )


def test_validate_with_invalid_type_alias():
    with pytest.raises(ValueError, match="targets must be one of"):
        vlmd_validate(CUSTOM_TYPES_CSV, type_aliases={"Whole Number": "whole"})


def test_extract_csv_to_csv_with_type_aliases(tmp_path):
    assert vlmd_extract(
        CUSTOM_TYPES_CSV,
        file_type="csv",
        output_dir=tmp_path,
        output_type="csv",
        type_aliases=CUSTOM_TYPE_ALIASES,
    )
    output = pd.read_csv(tmp_path / "heal-dd_vlmd_custom_types.csv", dtype=str)
    assert output["type"].tolist() == ["integer", "date", "string", "number"]
    assert output["description"][0] == "Age in years as a Whole Number"


def test_extract_with_invalid_type_alias(tmp_path):
    with pytest.raises(ExtractionError, match="targets must be one of"):
        vlmd_extract(
            CUSTOM_TYPES_CSV,
            output_dir=tmp_path,
            type_aliases={"Whole Number": "whole"},
        )
