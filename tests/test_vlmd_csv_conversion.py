from heal.vlmd.extract.csv_dict_conversion import convert_datadict_csv


def test_csv_conversion_valid_file(valid_csv_output, valid_converted_csv_to_json):
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.csv"
    data_dictionary_props = {}

    result = convert_datadict_csv(
        input_file, data_dictionary_props=data_dictionary_props
    )
    assert list(result.keys()) == ["templatejson", "templatecsv"]
    assert list(result.get("templatejson").keys()) == ["fields"]
    assert list(result.get("templatecsv").keys()) == ["fields"]
    assert result.get("templatejson") == valid_converted_csv_to_json
    assert result.get("templatecsv") == valid_csv_output


def test_csv_conversion_valid_data(
    valid_array_data, valid_csv_output, valid_converted_csv_to_json
):
    data_dictionary_props = {}
    result = convert_datadict_csv(
        valid_array_data, data_dictionary_props=data_dictionary_props
    )
    assert list(result.keys()) == ["templatejson", "templatecsv"]
    assert list(result.get("templatejson").keys()) == ["fields"]
    assert list(result.get("templatecsv").keys()) == ["fields"]
    assert result.get("templatejson") == valid_converted_csv_to_json
    assert result.get("templatecsv") == valid_csv_output
