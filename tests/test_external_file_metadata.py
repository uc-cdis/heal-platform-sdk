import pytest
import requests
import requests_mock
from unittest.mock import patch, MagicMock

from heal.external_file_metadata_generator import (
    query_dataverse_files,
    generate_external_file_metadata,
    send_metadata_to_api,
)


@pytest.fixture
def dataverse_response():
    return {
        "data": {
            "latestVersion": {
                "files": [
                    {"dataFile": {"id": 10244606}},
                    {"dataFile": {"id": 10244605}},
                    {"dataFile": {"id": 10244608}},
                    {"dataFile": {"id": 10244607}},
                ]
            }
        }
    }


@pytest.fixture
def mock_bearer_token(monkeypatch):
    monkeypatch.setenv("BEARER_TOKEN", "test_token")


def test_query_dataverse_files(dataverse_response):
    with requests_mock.Mocker() as m:
        persistent_id = "doi:10.7910/DVN/PC5QR0"
        url = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={persistent_id}"
        m.get(url, json=dataverse_response, status_code=200)

        files = query_dataverse_files(persistent_id)

        assert len(files) == 4
        assert files[0]["dataFile"]["id"] == 10244606


def test_query_dataverse_files_failure():
    with requests_mock.Mocker() as m:
        persistent_id = "invalid_id"
        url = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={persistent_id}"
        m.get(url, status_code=404, text="Not Found")

        files = query_dataverse_files(persistent_id)

        assert files is None


def test_generate_external_file_metadata(dataverse_response):
    files = dataverse_response["data"]["latestVersion"]["files"]
    metadata = generate_external_file_metadata(files)

    expected_metadata = [
        {
            "external_oidc_idp": "dataverse-keycloak",
            "file_retriever": "Dataverse",
            "file_id": "10244606",
        },
        {
            "external_oidc_idp": "dataverse-keycloak",
            "file_retriever": "Dataverse",
            "file_id": "10244605",
        },
        {
            "external_oidc_idp": "dataverse-keycloak",
            "file_retriever": "Dataverse",
            "file_id": "10244608",
        },
        {
            "external_oidc_idp": "dataverse-keycloak",
            "file_retriever": "Dataverse",
            "file_id": "10244607",
        },
    ]

    assert metadata == expected_metadata


def test_send_metadata_to_api_success(mock_bearer_token):
    metadata = [
        {
            "file_id": "10244606",
            "file_retriever": "Dataverse",
            "external_oidc_idp": "dataverse-keycloak",
        }
    ]
    study_id = "HDP00249"

    with requests_mock.Mocker() as m:
        target_url = f"https://qa-heal.planx-pla.net/mds/metadata/{study_id}?merge=true"
        m.put(target_url, status_code=200)

        send_metadata_to_api(metadata, study_id)

        assert m.called
        assert m.last_request.json() == {"external_file_metadata": metadata}


def test_send_metadata_to_api_failure(mock_bearer_token):
    metadata = [
        {
            "file_id": "10244606",
            "file_retriever": "Dataverse",
            "external_oidc_idp": "dataverse-keycloak",
        }
    ]
    study_id = "HDP00249"

    with requests_mock.Mocker() as m:
        target_url = f"https://qa-heal.planx-pla.net/mds/metadata/{study_id}?merge=true"
        m.put(target_url, status_code=500, text="Internal Server Error")

        send_metadata_to_api(metadata, study_id)

        assert m.called
        assert m.last_request.json() == {"external_file_metadata": metadata}


def test_send_metadata_to_api_missing_token():
    metadata = [
        {
            "file_id": "10244606",
            "file_retriever": "Dataverse",
            "external_oidc_idp": "dataverse-keycloak",
        }
    ]
    study_id = "HDP00249"

    # Mock an empty environment
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(SystemExit):
            send_metadata_to_api(metadata, study_id)
