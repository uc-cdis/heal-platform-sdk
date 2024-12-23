import pytest
from heal.vlmd.extract.json_dict_conversion import convert_templatejson


def test_json_conversion_valid_file(valid_json_output):
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    input_type = "json-template"
    valid_json_output.pop("schemaVersion", None)

    result = convert_templatejson(input_file)
    assert list(result.keys()) == ["templatejson", "templatecsv"]
    assert list(result.get("templatejson").keys()) == [
        "title",
        "description",
        "fields",
    ]
    assert list(result.get("templatecsv").keys()) == ["title", "description", "fields"]
    assert result.get("templatejson") == valid_json_output


def test_json_conversion_valid_data(valid_json_data, valid_json_output):
    valid_json_output.pop("schemaVersion", None)
    result = convert_templatejson(valid_json_data)
    assert list(result.keys()) == ["templatejson", "templatecsv"]
    assert list(result.get("templatejson").keys()) == [
        "title",
        "description",
        "fields",
    ]
    assert list(result.get("templatecsv").keys()) == ["title", "description", "fields"]
    assert result.get("templatejson") == valid_json_output


@pytest.mark.parametrize("unallowed_input", [(["some", "list"], ("some", "set"), 5)])
def test_json_conversion_unallowed_input(unallowed_input):
    with pytest.raises(ValueError) as e:
        convert_templatejson(unallowed_input)

    expected_message = (
        "jsontemplate needs to be either dictionary-like or a path to a json"
    )
    assert expected_message in str(e.value)