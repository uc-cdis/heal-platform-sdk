# VLMD methods

## VLMD validation

This module validates VLMD data dictionaries against stored schemas. The `vlmd_validate()` method
will attempt an extraction as part of the validation process.

The `vlmd_validate()` method raises a `jsonschema.ValidationError` for an invalid input file and
will raise an `ExtractionError` if the input_file cannot be converted

Example validation code:

```
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

The current formats are csv, json, and tsv.

The `vlmd_extract()` method raises a `jsonschema.ValidationError` for an invalid input files
and raises an `ExtractionError` for any other type of error.

Example extraction code:

```
from jsonschema import ValidationError

from heal.vlmd import vlmd_extract, ExtractionError

try:
  vlmd_extract("vlmd_for_extraction.csv", output_dir="./output")

except ValidationError as v_err:
  # handle validation error

except ExtractionError as e_err:
  # handle extraction error
```

The above will write a HEAL-compliant VLMD json dictionary to

`output/heal-dd_vlmd_for_extraction.json`

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
