# VLMD methods

## VLMD validation

This module validates VLMD data dictionaries against stored schemas.

The `vlmd_validate()` method raises a `jsonschema.ValidationError` for an invalid input file.

Example validation code:

```
from jsonschema import ValidationError

from heal.vlmd import vlmd_validate

input_file = "vlmd_dd.json"
try:
    vlmd_validate(input_file)
except ValidationError as e:
    # handle validation error

```

### Adding new validators

The module currently validates the following types of dictionaries: csv, json, tsv.

To add code for a new dictionary file type:

* Create a new schema for the data type or validate against the existing json schema
* Create a new validator module for the new file type
* Call the new module from the `validator.py` module
* Create unit tests as needed for new code
