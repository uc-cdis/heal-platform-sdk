import os
from pathlib import Path
import requests
from typing import Dict, List, Tuple
from unittest import mock

import pytest
import requests_mock
from unittest.mock import MagicMock

from gen3.tools.download.drs_download import DownloadStatus, wts_get_token
from heal.qdr_downloads import (
    download_from_url,
    get_download_url_for_qdr,
    get_filename_from_headers,
    get_id,
    get_idp_access_token,
    get_request_headers,
    get_syracuse_qdr_files,
    is_valid_qdr_file_metadata,
)


@pytest.fixture(scope="session")
def download_dir(tmpdir_factory):
    path = tmpdir_factory.mktemp("qdr_download_dir")
    return path


@pytest.fixture
def wts_hostname():
    return "test.commons.io"


@pytest.mark.parametrize(
    "file_metadata",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            }
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            }
        ),
    ],
)
def test_is_valid_qdr_file_metadata(file_metadata: Dict):
    assert is_valid_qdr_file_metadata(file_metadata) == True


def test_is_valid_qdr_file_metadata_failed():
    # missing keys
    file_metadata = (
        {
            "external_oidc_idp": "test-external-idp",
            "file_retriever": "QDR",
            "description": "missing study_id or file_id",
        },
    )
    assert is_valid_qdr_file_metadata(file_metadata) == False

    # has both study_id and file_id keys
    file_metadata = (
        {
            "external_oidc_idp": "test-external-idp",
            "file_retriever": "QDR",
            "file_id": "QDR_file_02",
            "study_id": "QDR_file_02",
        },
    )
    assert is_valid_qdr_file_metadata(file_metadata) == False

    # not a dict
    file_metadata = ("file_metadata_is_not_a_dict",)
    assert is_valid_qdr_file_metadata(file_metadata) == False


@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            },
            "QDR_study_01",
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
            "QDR_file_02",
        ),
    ],
)
def test_get_id(file_metadata: Dict, expected: str):
    assert get_id(file_metadata) == expected


def test_get_id_bad_input():
    # missing study_id and file_id
    file_metadata = {
        "external_oidc_idp": "test-external-idp",
        "file_retriever": "QDR",
    }
    assert get_id(file_metadata) == None


def test_get_idp_access_token(wts_hostname):
    test_idp = "extermal-keycloak"
    file_metadata = {
        "external_oidc_idp": test_idp,
        "file_retriever": "QDR",
        "study_id": "QDR_study_01",
    }
    returned_idp_token = "some-idp-token"
    mock_auth = MagicMock()
    mock_auth.get_access_token.return_value = "some_token"
    with requests_mock.Mocker() as m:
        m.get(
            f"https://{wts_hostname}/wts/token/?idp={test_idp}",
            json={"token": returned_idp_token},
        )
        with mock.patch(
            "gen3.tools.download.drs_download.wts_get_token"
        ) as wts_get_token:
            wts_get_token.return_value = returned_idp_token
            assert (
                get_idp_access_token(
                    wts_hostname=wts_hostname,
                    auth=mock_auth,
                    file_metadata=file_metadata,
                )
                == returned_idp_token
            )


def test_get_request_headers_for_study_or_file():
    mock_idp_token = "some-idp-token"

    # idp_token is present - just the bearer token
    expected_headers = {"Authorization": f"Bearer {mock_idp_token}"}
    assert get_request_headers(idp_access_token=mock_idp_token) == expected_headers

    # missing idp token - empty headers
    assert get_request_headers(idp_access_token=None) == {}


@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "study_id": "QDR_study_01",
            },
            "https://data.qdr.syr.edu/api/access/dataset/:persistentId/?persistentId=QDR_study_01",
        ),
        (
            {
                "file_id": "QDR_file_02",
            },
            "https://data.qdr.syr.edu/api/access/datafile/QDR_file_02",
        ),
    ],
)
def test_get_download_url_for_qdr(file_metadata: Dict, expected: str):
    assert get_download_url_for_qdr(file_metadata) == expected


@pytest.mark.parametrize(
    "file_metadata_qdr_staging, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
                "use_qdr_staging": True,
            },
            "https://data.stage.qdr.org/api/access/dataset/:persistentId/?persistentId=QDR_study_01",
        )
    ],
)
def test_get_download_url_for_qdr_staging(
    file_metadata_qdr_staging: Dict, expected: str
):
    assert get_download_url_for_qdr(file_metadata_qdr_staging) == expected


def test_get_download_url_for_qdr_failed():
    # missing file_ids or study_id
    file_metadata = {}
    assert get_download_url_for_qdr(file_metadata) == None


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
        qdr_url = "https://data.qdr.test.edu/api/access/:persistentId/?persistentId=QDR_study_01"
        valid_response_headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": f"application; filename={mock_zip_file_name}",
        }
        m.get(
            qdr_url, headers=valid_response_headers, content=bytes(mock_data, "utf-8")
        )
        download_filename = download_from_url(
            qdr_url=qdr_url,
            headers=request_headers,
            download_path=download_dir,
        )
        assert download_filename == f"{download_dir}/{mock_zip_file_name}"
        assert os.path.exists(download_filename)
        with open(download_filename, "r") as f:
            assert f.read() == mock_data

        # get file_id
        mock_file_id = "123456"
        mock_filename = "some_file.pdf"
        valid_response_headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": f"application; filename*=UTF-8''{mock_filename}",
        }
        qdr_url = f"https://data.qdr.test.edu/api/access/datafile/{mock_file_id}"
        m.get(
            qdr_url, headers=valid_response_headers, content=bytes(mock_data, "utf-8")
        )

        download_filename = download_from_url(
            qdr_url=qdr_url,
            headers=request_headers,
            download_path=download_dir,
        )
        # filename is from response headers, not file_id
        assert download_filename == f"{download_dir}/{mock_filename}"
        assert os.path.exists(download_filename)
        with open(download_filename, "r") as f:
            assert f.read() == mock_data

        # cannot get downloaded file name from header - fall back to file id
        response_headers = {
            "Content-Disposition": "application; ",
        }
        m.get(qdr_url, headers=response_headers, content=bytes(mock_data, "utf-8"))

        download_filename = download_from_url(
            qdr_url=qdr_url,
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
        qdr_url="https://bad_url",
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
        qdr_url = "https://data.qdr.test.edu/api/access/datafiles/some_id"
        m.get(
            qdr_url, headers=valid_response_headers, content=bytes(mock_data, "utf-8")
        )

        download_file = download_from_url(
            qdr_url=qdr_url,
            headers=request_headers,
            download_path="/path/does/not/exist",
        )
        assert download_file == None
        assert not os.path.exists(download_filename)

        # zero size response
        m.get(qdr_url, headers=valid_response_headers, content=bytes())
        download_file = download_from_url(
            qdr_url=qdr_url,
            headers=request_headers,
            download_path=download_dir,
        )
        assert download_file == None
        assert (os.path.getsize(download_filename)) == 0
        Path(download_filename).unlink()


def test_get_syracuse_qdr_files(wts_hostname, download_dir):
    test_idp = "test-external-idp"
    test_data = "foo"

    # valid input and successful download
    test_file_id = "some_id"
    file_metadata_list = [
        {
            "external_oidc_idp": test_idp,
            "file_retriever": "QDR",
            "file_id": test_file_id,
        },
    ]
    expected_status = {
        test_file_id: DownloadStatus(filename=test_file_id, status="downloaded")
    }

    returned_idp_token = "some-idp-token"
    mock_auth = MagicMock()
    mock_auth.get_access_token.return_value = "some_token"
    valid_response_headers = {"Content-Type": "application/pdf"}
    with requests_mock.Mocker() as m, mock.patch(
        "gen3.tools.download.drs_download.wts_get_token"
    ) as wts_get_token:
        m.get(
            f"https://{wts_hostname}/wts/token/?idp={test_idp}",
            json={"token": returned_idp_token},
        )
        m.get(
            f"https://data.qdr.syr.edu/api/access/datafile/{test_file_id}",
            headers=valid_response_headers,
            content=bytes(test_data, "utf-8"),
        )
        wts_get_token.return_value = "some-idp-token"
        result = get_syracuse_qdr_files(
            wts_hostname=wts_hostname,
            auth=mock_auth,
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )
        assert result == expected_status


@pytest.mark.parametrize(
    "file_metadata_list",
    [
        ({"not": "a list"},),
        (["not", "dict", "items"],),
        (
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "missing": "file_id key",
                }
            ],
        ),
    ],
)
def test_get_syracuse_qdr_files_bad_input(
    wts_hostname, download_dir, file_metadata_list
):
    mock_auth = MagicMock()
    mock_auth.get_access_token.return_value = "some_token"

    result = get_syracuse_qdr_files(
        wts_hostname=wts_hostname,
        auth=mock_auth,
        file_metadata_list=file_metadata_list,
        download_path=download_dir,
    )
    assert result == None


def test_get_syracuse_qdr_files_no_url(wts_hostname, download_dir):
    test_file_id = "some_id"
    file_metadata_list = [
        {
            "external_oidc_idp": "test-external-idp",
            "file_retriever": "QDR",
            "file_id": test_file_id,
        },
    ]
    expected_status_invalid_url = {
        test_file_id: DownloadStatus(filename=test_file_id, status="invalid url")
    }
    mock_auth = MagicMock()
    mock_auth.get_access_token.return_value = "some_token"
    with mock.patch(
        "heal.qdr_downloads.get_download_url_for_qdr"
    ) as mock_get_download_url_for_qdr:
        # failed get_download_url
        mock_get_download_url_for_qdr.return_value = None

        result = get_syracuse_qdr_files(
            wts_hostname=wts_hostname,
            auth=mock_auth,
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )
        assert result == expected_status_invalid_url


def test_get_syracuse_qdr_files_failed_download(wts_hostname, download_dir):
    idp = "test-external-idp"
    test_data = "foo"

    # valid input
    test_file_id = "some_id"
    file_metadata_list = [
        {
            "external_oidc_idp": "test-external-idp",
            "file_retriever": "QDR",
            "file_id": test_file_id,
        },
    ]
    expected_status = {
        test_file_id: DownloadStatus(filename=test_file_id, status="failed")
    }

    returned_idp_token = "some-idp-token"
    mock_auth = MagicMock()
    mock_auth.get_access_token.return_value = "some_token"
    valid_response_headers = {"Content-Type": "application/zip"}
    with requests_mock.Mocker() as m, mock.patch(
        "gen3.tools.download.drs_download.wts_get_token"
    ) as wts_get_token:
        m.get(
            f"https://{wts_hostname}/wts/token/?idp={idp}",
            json={"token": returned_idp_token},
        )
        m.get(
            "https://data.qdr.syr.edu/api/access/datafile/{test_file_id}",
            headers=valid_response_headers,
            content=bytes(test_data, "utf-8"),
        )
        with mock.patch(
            "heal.qdr_downloads.download_from_url"
        ) as mock_download_from_url:
            # failed download
            mock_download_from_url.return_value = None

            result = get_syracuse_qdr_files(
                wts_hostname=wts_hostname,
                auth=mock_auth,
                file_metadata_list=file_metadata_list,
                download_path=download_dir,
            )
            assert result == expected_status
