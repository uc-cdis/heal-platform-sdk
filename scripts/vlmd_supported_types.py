"""
Generate a table of the variable `type` values that VLMD conversion accepts.

One row per type allowed by the HEAL csv schema, with:

    type               the value to put in the `type` column of a csv data dictionary
    description        the schema's definition of the type
    accepted_aliases   other spellings that conversion recodes to this type
    validation_checks  what validation checks about a field of this type
    redcap_sources     the REDCap field types (and validation types) that convert to it

The table is built from the code itself: the schema enum, the recode map in
`heal.vlmd.mappings`, and the REDCap mapping functions, which are called with
sample REDCap fields. The committed copy lives at docs/vlmd_supported_types.csv
and tests/test_vlmd_supported_types.py fails if it is out of date.

Usage:
    poetry run python scripts/vlmd_supported_types.py -o docs/vlmd_supported_types.csv
"""

import argparse
import csv
import io
import re
import sys

from heal.vlmd.config import CSV_SCHEMA
from heal.vlmd.mappings import recode_map
from heal.vlmd.mappings.redcap_csv_headers import (
    CHOICES_FIELD_NAME,
    TEXT_VALID_FIELD_NAME,
)
from heal.vlmd.mappings.redcap_field_mapping import type_mappings

COLUMNS = [
    "type",
    "description",
    "accepted_aliases",
    "validation_checks",
    "redcap_sources",
]

# REDCap's built-in "Text Validation Type" values. These aren't listed anywhere in
# the code (map_text matches on substrings such as "date" and "number"), so this
# is the one hand-maintained input to the table.
REDCAP_TEXT_VALIDATIONS = [
    "",
    "date_dmy",
    "date_mdy",
    "date_ymd",
    "datetime_dmy",
    "datetime_mdy",
    "datetime_ymd",
    "datetime_seconds_dmy",
    "datetime_seconds_mdy",
    "datetime_seconds_ymd",
    "time",
    "time_hh_mm_ss",
    "time_mm_ss",
    "integer",
    "number",
    "number_1dp",
    "number_2dp",
    "number_3dp",
    "number_4dp",
    "number_comma_decimal",
    "number_1dp_comma_decimal",
    "number_2dp_comma_decimal",
    "number_3dp_comma_decimal",
    "number_4dp_comma_decimal",
    "alpha_only",
    "email",
    "phone",
    "phone_australia",
    "postalcode_australia",
    "postalcode_canada",
    "postalcode_french",
    "postalcode_germany",
    "ssn",
    "vmrn",
    "zipcode",
]

# For a slider, REDCap uses the same column for "Show Slider Number".
REDCAP_SLIDER_VALIDATIONS = ["", "integer", "number"]

# Sample "Choices" values for field types whose output type depends on them.
REDCAP_CHOICES = {
    "numeric codes": "1, Yes | 2, No",
    "non-numeric codes": "y, Yes | n, No",
}


def _redcap_field(field_type, validation="", choices=""):
    """A REDCap row as map_* functions see it after rename_and_fill()."""
    return {
        "name": "example",
        "type": field_type,
        TEXT_VALID_FIELD_NAME: validation,
        CHOICES_FIELD_NAME: choices,
        "text_valid_min": "1",
        "text_valid_max": "9",
    }


def _redcap_samples(field_type):
    """Yield (label, sample REDCap field) pairs worth probing for a field type."""
    if field_type == "text":
        for validation in REDCAP_TEXT_VALIDATIONS:
            label = f"text[{validation}]" if validation else "text"
            yield label, _redcap_field(field_type, validation)
    elif field_type == "slider":
        for validation in REDCAP_SLIDER_VALIDATIONS:
            label = f"slider[{validation}]" if validation else "slider"
            yield label, _redcap_field(field_type, validation)
    elif field_type in ("dropdown", "radio"):
        for description, choices in REDCAP_CHOICES.items():
            label = f"{field_type} ({description})"
            yield label, _redcap_field(field_type, choices=choices)
    elif field_type == "checkbox":
        label = "checkbox (one field per choice)"
        yield label, _redcap_field(field_type, choices=REDCAP_CHOICES["numeric codes"])
    else:
        yield field_type, _redcap_field(field_type)


def _describe_redcap_props(props, field):
    """Summarise what a REDCap mapping adds besides the type, e.g. a pattern."""
    details = []
    if props.get("format"):
        details.append(f"format={props['format']}")
    constraints = props.get("constraints") or {}
    if constraints.get("pattern"):
        details.append(f"pattern={constraints['pattern']}")
    if constraints.get("minimum") is not None or constraints.get("maximum") is not None:
        details.append("min/max from Text Validation Min/Max")
    enum = constraints.get("enum")
    if enum:
        sample_codes = [
            item.split(",")[0].strip() for item in field[CHOICES_FIELD_NAME].split("|")
        ]
        if enum == sample_codes:
            details.append("enum from Choices")
        else:
            details.append(f"enum={'/'.join(enum)}")
    return f" ({', '.join(details)})" if details else ""


def redcap_sources_by_type():
    """
    Map each VLMD type to the REDCap sources that produce it, by calling the
    REDCap mapping functions on sample fields. Samples that raise are reported
    on stderr and left out of the table.
    """
    sources = {}
    for field_type, mapper in type_mappings.items():
        for label, field in _redcap_samples(field_type):
            try:
                result = mapper(field)
            except Exception as err:
                print(
                    f"warning: REDCap {label} could not be converted: {err!r}",
                    file=sys.stderr,
                )
                continue
            if result is None:
                continue
            # A checkbox becomes one field per choice.
            for props in result if isinstance(result, list) else [result]:
                entry = label + _describe_redcap_props(props, field)
                entries = sources.setdefault(props["type"], [])
                if entry not in entries:
                    entries.append(entry)
    return sources


def type_descriptions():
    """
    Parse the per-type definitions out of the schema's `additionalDescription`,
    which reads like "enum definitions: -  `number` (A numeric value ... (e.g., 3.14)) - ...".
    """
    text = CSV_SCHEMA["properties"]["type"].get("additionalDescription", "")
    text = text.replace('\\"', '"')
    parts = re.split(r"-\s+`(\w+)`\s+", text)
    descriptions = {}
    for name, description in zip(parts[1::2], parts[2::2]):
        description = description.strip()
        if description.startswith("("):
            description = description[1:]
        if description.count(")") > description.count("("):
            description = description[: description.rindex(")")]
        descriptions[name] = description.strip()
    return descriptions


def validation_checks(vlmd_type, aliases):
    accepted = [vlmd_type] + aliases
    return (
        "In a csv data dictionary the value is trimmed, lowercased, and has '_' and"
        " spaces replaced by '-', and must then be one of: "
        + ", ".join(f"'{value}'" for value in accepted)
        + ". A blank type is also allowed. Nothing checks that `format` or"
        " `constraints` suit the type, and data values are not checked against it."
    )


def build_rows():
    vlmd_types = CSV_SCHEMA["properties"]["type"]["enum"]
    descriptions = type_descriptions()
    redcap_sources = redcap_sources_by_type()
    aliases = {}
    for alias, vlmd_type in recode_map["type"].items():
        aliases.setdefault(vlmd_type, []).append(alias)

    rows = []
    for vlmd_type in vlmd_types:
        type_aliases = aliases.get(vlmd_type, [])
        rows.append(
            {
                "type": vlmd_type,
                "description": descriptions.get(vlmd_type, ""),
                "accepted_aliases": "|".join(type_aliases),
                "validation_checks": validation_checks(vlmd_type, type_aliases),
                "redcap_sources": "|".join(redcap_sources.get(vlmd_type, [])),
            }
        )
    return rows


def to_csv(rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "-o", "--output", help="CSV file to write (default: standard output)"
    )
    args = parser.parse_args()

    text = to_csv(build_rows())
    if args.output:
        with open(args.output, "w", newline="") as output_file:
            output_file.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
