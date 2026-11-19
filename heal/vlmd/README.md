# VLMD methods

*Please see our [full documentation on VLMD here](https://heal.github.io/platform-documentation/vlmd/vlmd_tools/)*

## CLI

The CLI can be invoked as follows

`heal [OPTIONS] COMMAND [ARGS]`

For a list of VLMD commands and options run

`heal vlmd --help`

For example, the following can validate a VLMD file in csv format:

`heal vlmd validate --input_file "vlmd_for_validation.csv"`

The following would extract a json format VLMD file from a csv format input file and
write a json file in the directory `output`:

`heal vlmd extract --input_file "vlmd_for_extraction.csv" --title "The dictionary title" --output_dir "./output"`

The `--title` option is required when extracting from `csv` to `json`.

The default output file type is `json`. Use the `--output_type` option for other output.
To get a `csv` output dictionary include `--output_type csv`. To get both `csv` and `json`
use a comma separated list of values such as `--output_type "csv, json"`.


## VLMD validation

This module validates VLMD data dictionaries against stored schemas. The `vlmd_validate()` method
will attempt an extraction as part of the validation process.

The `vlmd_validate()` method raises a `jsonschema.ValidationError` for an invalid input file and
will raise an `ExtractionError` if the input_file cannot be converted

Example validation code:

```python
from jsonschema import ValidationError

from heal.vlmd import vlmd_validate, ExtractionError

input_file = "vlmd_dd.json"
try:
    vlmd_validate(input_file)

except ValidationError as v_err:
    # handle validation error

except ExtractionError as e_err:
    # handle extraction error

```

## VLMD extract

The extract module implements extraction and conversion of dictionaries into different formats.

The current formats are csv, json, and tsv. A `title=<TITLE>` paramater should be supplied when
converting from non-json to json format.

The `vlmd_extract()` method raises a `jsonschema.ValidationError` for an invalid input files
and raises an `ExtractionError` for any other type of error.

Example extraction code:

```python
from jsonschema import ValidationError

from heal.vlmd import vlmd_extract, ExtractionError

try:
    vlmd_extract(
        "vlmd_for_extraction.csv",
        title="the dictionary title",
        output_dir="./output"
    )

except ValidationError as v_err:
    # handle validation error

except ExtractionError as e_err:
    # handle extraction error
```

The above will write a HEAL-compliant VLMD json dictionary to

`output/heal-dd_vlmd_for_extraction.json`

 The default output file type is `json`. Use the `output_type` paramater for other output. To get a csv output dictionary include `output_type="csv"`. To get both `csv` and `json`, use a list for the parameter values, such as
 ```python
 output_type=["csv", "json"]
 ```

## Supported variable types

[`docs/vlmd_supported_types.csv`](../../docs/vlmd_supported_types.csv) lists every value
allowed in the `type` column of a csv dictionary, the aliases that are recoded to it
(e.g. `int` to `integer`), what validation checks, and which REDCap field types convert to it.
It is generated from the schema and the mappings, so regenerate it after changing either:

```bash
poetry run python scripts/vlmd_supported_types.py -o docs/vlmd_supported_types.csv
```

`tests/test_vlmd_supported_types.py` fails if the committed copy is out of date.

Things that commonly trip people up:

* Before checking, a `type` value is trimmed, lowercased, and has `_` and spaces replaced by
  `-`. So `Integer` is accepted, but `date_time` (which becomes `date-time`) and `year month`
  are not.
* Only the spelling of `type` is checked. Nothing checks that `format` or `constraints`
  suit the type.
* From REDCap, `sql` and `descriptive` fields (and any unrecognised field type) are dropped
  without a warning, and a `slider` with no "Text Validation Type OR Show Slider Number" value
  currently fails to convert.

## Adding new file types for extraction and validation

The above moduels currently handle the following types of dictionaries: csv, json, tsv.

To add code for a new dictionary file type:

* Create a new schema for the data type or validate against the existing json schema
* If possible create a new validator module for the new file type
* Call the new validator module from the `validate.py` module
* Create a new extractor module for the new file type, possibly using `pandas`
* Call the new extractor module from the `conversion.py` module
* Add new file writing utilities if saving converted dictionaries in the new format
* Create unit tests as needed for new code
