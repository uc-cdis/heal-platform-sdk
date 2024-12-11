import os
from pathlib import Path
import requests
from typing import Dict, List, Tuple
from unittest import mock

import pytest
import requests_mock
from unittest.mock import MagicMock

from gen3.tools.download.drs_download import DownloadStatus
from heal.harvard_downloads import (
    is_valid_harvard_file_metadata,
    get_id,
    get_download_url_for_harvard_dataverse,
    get_filename_from_headers,
    download_from_url,
    get_harvard_dataverse_files,
)


@pytest.fixture(scope="session")
def download_dir(tmpdir_factory):
    path = tmpdir_factory.mktemp("harvard_download_dir")
    return path


@pytest.mark.parametrize(
    "file_metadata",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "harvard",
                "study_id": "harvard_study_01",
            }
        ),
    ],
)
def test_is_valid_harvard_file_metadata(file_metadata: Dict):
    assert is_valid_harvard_file_metadata(file_metadata) == True


def test_is_valid_harvard_file_metadata_failed():
    # missing keys
    file_metadata = (
        {
            "external_oidc_idp": "test-external-idp",
            "file_retriever": "harvard",
            "description": "missing study_id or file_id",
        },
    )
    assert is_valid_harvard_file_metadata(file_metadata) == False

    # not a dict
    file_metadata = ("file_metadata_is_not_a_dict",)
    assert is_valid_harvard_file_metadata(file_metadata) == False


@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "harvard",
                "study_id": "harvard_study_01",
            },
            "harvard_study_01",
        ),
    ],
)
def test_get_id(file_metadata: Dict, expected: str):
    assert get_id(file_metadata) == expected


def test_get_id_bad_input():
    # missing study_id
    file_metadata = {
        "external_oidc_idp": "test-external-idp",
        "file_retriever": "harvard",
    }
    assert get_id(file_metadata) == None


@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "study_id": "harvard_study_01",
            },
            "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=harvard_study_01",
        ),
    ],
)
def test_get_download_url_for_qdr(file_metadata: Dict, expected: str):
    assert get_download_url_for_harvard_dataverse(file_metadata) == expected


@pytest.mark.parametrize(
    "file_metadata_harvard_staging, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "harvard",
                "study_id": "harvard_study_01",
                "use_harvard_staging": True,
            },
            "https://demo.dataverse.org/api/access/dataset/:persistentId/?persistentId=harvard_study_01",
        )
    ],
)
def test_get_download_url_for_harvard_staging(
    file_metadata_harvard_staging: Dict, expected: str
):
    assert (
        get_download_url_for_harvard_dataverse(file_metadata_harvard_staging)
        == expected
    )


def test_get_download_url_for_harvard_failed():
    # missing file_ids or study_id
    file_metadata = {}
    assert get_download_url_for_harvard_dataverse(file_metadata) == None


def test_get_filename_from_headers():
    # zip file for study_id
    mock_zip_file_name = "test.zip"
    mock_response_headers = {
        "Content-Type": "application/zip",
        "Content-Disposition": f"application; filename={mock_zip_file_name}",
    }
    assert get_filename_from_headers(mock_response_headers) == mock_zip_file_name

    # utf-8 encoded file name for file_id
    mock_file_name = "test.pdf"
    mock_response_headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"application; filename*=UTF-8''{mock_file_name}",
    }
    assert get_filename_from_headers(mock_response_headers) == mock_file_name


def test_get_filename_from_headers_invalid():
    mock_response_headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"application; filename",
    }
    assert get_filename_from_headers(mock_response_headers) == None


def test_download_from_url(download_dir):
    request_headers = {"Authorization": "Bearer some-idp-token"}
    mock_data = "foo"

    with requests_mock.Mocker() as m:
        # get study_id
        mock_zip_file_name = "dataverse_files.zip"
        harvard_url = "https://dataverse.harvard.edu/api/access/:persistentId/?persistentId=harvard_study_01"
        valid_response_headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": f"application; filename={mock_zip_file_name}",
        }
        m.get(
            harvard_url,
            headers=valid_response_headers,
            content=bytes(mock_data, "utf-8"),
        )
        download_filename = download_from_url(
            harvard_url=harvard_url,
            headers=request_headers,
            download_path=download_dir,
        )
        assert download_filename == f"{download_dir}/{mock_zip_file_name}"
        assert os.path.exists(download_filename)
        with open(download_filename, "r") as f:
            assert f.read() == mock_data

        # cannot get downloaded file name from header - fall back to file id
        response_headers = {
            "Content-Disposition": "application; ",
        }
        m.get(harvard_url, headers=response_headers, content=bytes(mock_data, "utf-8"))
        mock_file_id = "123456"
        mock_filename = "some_file.pdf"
        harvard_url = (
            f"https://dataverse.harvard.edu/api/access/datafile/{mock_file_id}"
        )
        download_filename = download_from_url(
            harvard_url=harvard_url,
            headers=request_headers,
            download_path=download_dir,
        )
        # filename is from file_id
        assert download_filename != f"{download_dir}/{mock_filename}"
        assert download_filename == f"{download_dir}/{mock_file_id}"
        assert os.path.exists(download_filename)
        with open(download_filename, "r") as f:
            assert f.read() == mock_data


def test_download_from_url_failures(download_dir):
    request_headers = {"Authorization": "Bearer some-idp-token"}
    valid_response_headers = {"Content-Type": "application/zip"}
    mock_data = "foo"
    mock_zip_file_name = "dataverse_files.zip"
    download_filename = f"{download_dir}/dataverse_files.zip"
    if os.path.exists(download_filename):
        Path(download_filename).unlink()

    # bad url
    downloaded_file = download_from_url(
        harvard_url="https://bad_url",
        headers=request_headers,
        download_path=download_dir,
    )
    assert downloaded_file == None
    assert not os.path.exists(download_filename)

    with requests_mock.Mocker() as m:
        valid_response_headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": f"application; filename={mock_zip_file_name}",
        }

        # bad download path
        harvard_url = "https://data.qdr.test.edu/api/access/datafiles/some_id"
        m.get(
            harvard_url,
            headers=valid_response_headers,
            content=bytes(mock_data, "utf-8"),
        )

        download_file = download_from_url(
            harvard_url=harvard_url,
            headers=request_headers,
            download_path="/path/does/not/exist",
        )
        assert download_file == None
        assert not os.path.exists(download_filename)

        # zero size response
        m.get(harvard_url, headers=valid_response_headers, content=bytes())
        download_file = download_from_url(
            harvard_url=harvard_url,
            headers=request_headers,
            download_path=download_dir,
        )
        assert download_file == None
        assert (os.path.getsize(download_filename)) == 0
        Path(download_filename).unlink()


def test_get_harvard_dataverse_files(wts_hostname, download_dir):
    test_data = "foo"

    # valid input and successful download
    test_study_id = "some_id"
    file_metadata_list = [
        {
            "file_retriever": "harvard_dataverse",
            "study_id": test_study_id,
        },
    ]
    expected_status = {
        test_study_id: DownloadStatus(filename=test_study_id, status="downloaded")
    }

    valid_response_headers = {
        "Content-Disposition": f"attachment; filename={test_study_id}.zip",
        "Content-Type": "application/zip",
    }

    with requests_mock.Mocker() as m:
        # Mocking the Harvard Dataverse API endpoint
        m.get(
            f"https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId={test_study_id}",
            headers=valid_response_headers,
            content=bytes(test_data, "utf-8"),
        )

        # Call the function to test
        result = get_harvard_dataverse_files(
            wts_hostname=None,  # Not required for Harvard Dataverse
            auth=None,  # Not required for Harvard Dataverse
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )

        # Check if the result matches the expected status
        assert result == expected_status

        # Verify the file was saved
        downloaded_file_path = Path(download_dir) / f"{test_study_id}.zip"
        assert downloaded_file_path.exists()
        assert downloaded_file_path.read_text() == test_data
