import pytest

from heal.vlmd.extract.json_dict_conversion import convert_template_json


def test_json_conversion_valid_file(valid_json_output):
    input_file = "tests/test_data/vlmd/valid/vlmd_valid.json"
    valid_json_output.pop("schemaVersion", None)

    result = convert_template_json(input_file)
    assert list(result.keys()) == ["template_json", "template_csv"]
    assert list(result.get("template_json").keys()) == [
        "title",
        "description",
        "fields",
    ]
    assert list(result.get("template_csv").keys()) == ["title", "description", "fields"]
    assert result.get("template_json") == valid_json_output


def test_json_conversion_valid_data(valid_json_data, valid_json_output):
    valid_json_output.pop("schemaVersion", None)
    result = convert_template_json(valid_json_data)
    assert list(result.keys()) == ["template_json", "template_csv"]
    assert list(result.get("template_json").keys()) == [
        "title",
        "description",
        "fields",
    ]
    assert list(result.get("template_csv").keys()) == ["title", "description", "fields"]
    assert result.get("template_json") == valid_json_output


@pytest.mark.parametrize("unallowed_input", [(["some", "list"], ("some", "set"), 5)])
def test_json_conversion_unallowed_input(unallowed_input):
    with pytest.raises(ValueError) as e:
        convert_template_json(unallowed_input)

    expected_message = (
        "json_template needs to be either dictionary-like or a path to a json"
    )
    assert expected_message in str(e.value)
