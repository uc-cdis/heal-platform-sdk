# VLMD methods

## VLMD validate and extract

The validate_extract module implements both validation and conversion of dictionaries into different formats. Combining both validation and conversion in a single method verifies that
input dictionaries are valid and can be converted into valid HEAL-complient dictionaries.

The current input formats are csv/tsv and json. The current converted dictionary formats are csv and json.

The `vlmd_validate_extract()` method raises a `jsonschema.ValidationError` for invalid
input files and raises `ExtractionError` for errors in the conversion process.

Example validation/extraction code:

```
from jsonschema import ValidationError

from heal.vlmd.validate.validate_extract import vlmd_validate_extract

try:
  vlmd_validate_extract("vlmd_for_extraction.csv", output_dir="./output")

except ValidationError as v_err:
  # handle validation error

except ExtractionError as e_err:
  # handle extraction error
```

If the input is valid and can be converted, this writes a converted dictionary to

`output/heal-dd_vlmd_for_extraction.json`


## Adding new file types for extraction and validation

The above moduels currently handle the following types of dictionaries: csv, json, tsv.

To add code for a new dictionary file type:

* Create a new schema for the data type or validate against the existing json schema
* If possible, create a new validator method and call before `convert_to_vlmd`
* Create a new extractor module for the new file type, possibly using `pandas`
* Call the new extractor module from the `conversion.py` module
* Add new file writing utilities if saving converted dictionaries in the new format
* Create unit tests as needed for new code
