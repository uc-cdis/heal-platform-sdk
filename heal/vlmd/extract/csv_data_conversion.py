"""
CSV data to HEAL VLMD conversion
"""

from heal.vlmd.extract.json_dict_conversion import convert_template_json
from heal.vlmd.mappings import typesets
from heal.vlmd.validate.utils import read_delim


def convert_dataset_csv(file_path, data_dictionary_props={}):
    """
    Takes a CSV file containing data (not metadata) and
    infers each of it's variables data types and names.
    These inferred properties are then outputted as partially-completed
    HEAL variable level metadata files. That is, it outputs the `name` and `type` property.

    NOTE: this will be an invalid file as `description` is required
    for each variable. However, this serves as a great way to start
    the basis of a VLMD submission.
    """
    df = read_delim(file_path)
    data_dictionary = data_dictionary_props.copy()
    fields = typesets.infer_frictionless_fields(df)
    data_dictionary["fields"] = fields

    package = convert_template_json(data_dictionary)
    return package
