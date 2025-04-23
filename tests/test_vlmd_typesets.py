import pandas as pd
import pytest

from heal.vlmd.mappings.typesets import infer_frictionless_fields


def test_infer_frictionless_fields():
    """Test that types are inferred from a data frame"""

    test_data = {
        "id": [1, 2, 3, 4],
        "name": ["Ireland", "France", "Germany", "Fake"],
        "population": [67, 83, 60, 60],
        "is_cool_country": ["Yes", "No", "No", "Yes"],
        "coolness_scale": [2, 1, 1, 1],
    }
    df = pd.DataFrame(data=test_data)
    expected_fields = [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "population", "type": "integer"},
        {"name": "is_cool_country", "type": "boolean"},
        {"name": "coolness_scale", "type": "integer"},
    ]

    fields = infer_frictionless_fields(df)
    assert fields == expected_fields
