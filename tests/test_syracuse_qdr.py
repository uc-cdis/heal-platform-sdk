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
    check_ids_and_collate_file_ids,
    download_from_url,
    get_download_url_for_qdr,
    get_request_headers,
    get_request_body,
    get_syracuse_qdr_files,
    get_id,
    get_idp_access_token,
    get_request_type,
    is_valid_qdr_file_metadata
)

# TODO: check or create download path, use as fixture, eg "data"

@pytest.fixture
def wts_hostname():
    return "test.commons.io"

    
@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (            
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            }, 
            "GET"
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
            "GET"
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_ids": "QDR_file_01, QDR_file_02",
            },
            "POST"
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
            },
            None
        )
    ],
)
def test_get_request_type(file_metadata: Dict, expected: str):
    assert get_request_type(file_metadata) == expected

# TODO: split this into pass cases and fail cases
@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            },
            True,
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
            True,
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
            },
            False,
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
                "study_id": "QDR_file_02",
            },
            False,
        ),
        (
            "file_metadata_is_not_a_dict",
            False,
        ),
    ],
)
def test_is_valid_qdr_file_metadata(file_metadata: Dict, expected: bool):
    assert is_valid_qdr_file_metadata(file_metadata) == expected


@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            },
            "QDR_study_01"
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
            "QDR_file_02",
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_ids": "QDR_file_01,QDR_file_02",
            },
            "QDR_file_01,QDR_file_02",
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
            },
            None,
        ),
    ],
)
def test_get_id(file_metadata: Dict, expected: str):
    assert get_id(file_metadata) == expected


@pytest.mark.parametrize(
    "file_metadata, collate_file_ids, expected",
    [
        (
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "study_id": "QDR_study_01",
                },
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                }
            ],
            True,
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "study_id": "QDR_study_01",
                }
            ],
        ),
        (
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_id": "QDR_file_02",
                }
            ],
            True,
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_ids": "QDR_file_02",
                }
            ],
        ),
        (
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "study_id": "QDR_study_01",
                },
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_id": "QDR_file_02",
                },
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_id": "QDR_file_03",
                }
            ],
            True,
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "study_id": "QDR_study_01",
                },
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_ids": "QDR_file_02,QDR_file_03",
                },
            ],
        ),
        (
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "study_id": "QDR_study_01",
                },
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_id": "QDR_file_02",
                },
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_id": "QDR_file_03",
                }
            ],
            False,
            [
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "study_id": "QDR_study_01",
                },
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_id": "QDR_file_02",
                },
                {
                    "external_oidc_idp": "test-external-idp",
                    "file_retriever": "QDR",
                    "file_id": "QDR_file_03",
                }
            ],
        ),
    ],
)
def test_check_ids_and_collate_file_ids(file_metadata: Dict, collate_file_ids: bool, expected: Dict):
    assert check_ids_and_collate_file_ids(file_metadata, collate_file_ids) == expected


# TODO: just have 2 cases in test - don't parametrize
@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            },
            None,
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
            None,
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_ids": "QDR_file_01,QDR_file_02",
            },
            "fileIds=QDR_file_01,QDR_file_02",
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
            },
            None,
        ),
    ],
)
def test_get_request_body(file_metadata: Dict, expected: str):
    assert get_request_body(file_metadata) == expected


def test_get_idp_access_token(wts_hostname):
    # wts_hostname = "test.commons1.io"
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
            assert get_idp_access_token(
                wts_hostname=wts_hostname,
                auth = mock_auth,
                file_metadata = file_metadata
            ) == returned_idp_token


# TODO: just have 2 cases in test - don't parametrize
@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            },
            {"X-Dataverse-key": "some-idp-token"},
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
            {"X-Dataverse-key": "some-idp-token"},
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_ids": "QDR_file_01,QDR_file_02",
            },
            {
                "Content-Type": "text/plain",
                "X-Dataverse-key": "some-idp-token"
            },
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
            },
           {"X-Dataverse-key": "some-idp-token"},
        ),
    ],
)
def test_get_request_headers(wts_hostname: str, file_metadata: Dict, expected: str):
    # wts_hostname = "test.commons1.io"
    returned_idp_token = "some-idp-token"
    mock_auth = MagicMock()
    mock_auth.get_access_token.return_value = "some_token"
    with requests_mock.Mocker() as m:
        m.get(
            f"https://{wts_hostname}/wts/token/?idp={file_metadata.get('external_oidc_idp')}",
            json={"token": returned_idp_token},
        )
        with mock.patch(
            "gen3.tools.download.drs_download.wts_get_token"
        ) as wts_get_token:
            wts_get_token.return_value = "some-idp-token"
            assert get_request_headers(
                idp_access_token=returned_idp_token,
                file_metadata=file_metadata
            ) == expected

# TODO: add case of failure in getting access token. 

# TODO: split into 2 tests valid and failed
@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01"
            },
            "https://data.qdr.syr.edu/api/access/dataset/:persistentId/?persistentId=QDR_study_01",
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
           "https://data.qdr.syr.edu/api/access/datafiles/QDR_file_02",
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_ids": "QDR_file_01, QDR_file_02",
            },
            "https://data.qdr.syr.edu/api/access/datafiles",
        ),
        (
            {},
            None,
        ),
    ],
)
def test_get_download_url_for_qdr(file_metadata: Dict, expected: str):
    assert get_download_url_for_qdr(file_metadata) == expected


def test_download_from_url():
    request_headers = {"X-Dataverse-key": "some-idp-token"}
    valid_response_headers = { "Content-Type": "application/zip"}
    test_data = "foo"
    download_filename = "data/dataverse_files.zip"
    if os.path.exists(download_filename):
        Path(download_filename).unlink()

    with requests_mock.Mocker() as m:
        # get study_id
        qdr_url = "https://data.qdr.test.edu/api/access/:persistentId/?persistentId=QDR_study_01"
        m.get(
            qdr_url,
            headers = valid_response_headers,
            content = bytes(test_data, 'utf-8')
        )
        result = download_from_url(
            download_filename = download_filename,
            request_type = "GET",
            qdr_url = qdr_url,
            headers = request_headers,
            body = None,
        )
        assert result == True
        assert os.path.exists(download_filename)
        with open(download_filename, "r") as f:
            assert f.read() == test_data
        Path(download_filename).unlink()

        # post file_ids
        qdr_url = "https://data.qdr.test.edu/api/access/datafiles"
        m.post(
            qdr_url,
            headers = valid_response_headers,
            content = bytes(test_data, 'utf-8')
        )
        result = download_from_url(
            download_filename = download_filename,
            request_type = "POST",
            qdr_url = qdr_url,
            headers = request_headers,
            body = "fileIds=QDR_file_01,QDR_file_02",
        )
        assert result == True
        assert os.path.exists(download_filename)
        with open(download_filename, "r") as f:
            assert f.read() == test_data
        Path(download_filename).unlink()

        # zero size response
        m.post(
            qdr_url,
            headers = valid_response_headers,
            content = bytes()
        )
        result = download_from_url(
            download_filename = download_filename,
            request_type = "POST",
            qdr_url = qdr_url,
            headers = request_headers,
            body = "fileIds=QDR_file_01,QDR_file_02",
        )
        assert result == False
        assert not os.path.exists(download_filename)

        # bad download path
        m.post(
            qdr_url,
            headers = valid_response_headers,
            content = bytes(test_data, 'utf-8')
        )
        result = download_from_url(
            download_filename = "/path/does/not/exist",
            request_type = "POST",
            qdr_url = qdr_url,
            headers = request_headers,
            body = "fileIds=QDR_file_01,QDR_file_02",
        )
        assert result == False
        assert not os.path.exists(download_filename)

        # bad url
        m.post(
            "https://bad_url",
            headers = valid_response_headers,
            content = bytes(test_data, 'utf-8')
        )
        result = download_from_url(
            download_filename = "/path/does/not/exist",
            request_type = "POST",
            qdr_url = "https://bad_url",
            headers = request_headers,
            body = "fileIds=QDR_file_01,QDR_file_02",
        )
        assert result == False
        assert not os.path.exists(download_filename)


@pytest.mark.parametrize(
    "file_metadata_list, download_path",
    [
        (
            { "not": "a list" },
            "data"
        ),
        (
            ["not", "dict", "items"],
            "data"
        ),
        (
            [{
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "file_id_value"
            }],
            "download/path/does/not/exist"
        ),
        (
            [{
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "missing": "file_id key"
            }],
            "data"
        ),
    ],
)
def test_get_syracuse_qdr_files_bad_input(wts_hostname, file_metadata_list, download_path):

    expected = None
    # wts_hostname = "test.commons1.io"
    mock_auth = MagicMock()
    mock_auth.get_access_token.return_value = "some_token"

    result = get_syracuse_qdr_files(
        wts_hostname = wts_hostname,
        auth = mock_auth,
        file_metadata_list = file_metadata_list,
        download_path = download_path
    )
    assert result == expected


def test_get_syracuse_qdr_files(wts_hostname):

    # wts_hostname = "test.commons1.io"
    idp = "test-external-idp"
    test_data = "foo"

    # valid input and successful download
    file_metadata_list = [
        {
            "external_oidc_idp": "test-external-idp",
            "file_retriever": "QDR",
            "file_id": "QDR_file_02",
        },
        {
            "external_oidc_idp": "test-external-idp",
            "file_retriever": "QDR",
            "file_id": "QDR_file_03",
        }
    ]
    download_path = "data"
    expected_status = {
        "QDR_file_02,QDR_file_03": DownloadStatus(
            filename="QDR_file_02,QDR_file_03", status="downloaded"
        )
    }

    returned_idp_token = "some-idp-token"
    mock_auth = MagicMock()
    mock_auth.get_access_token.return_value = "some_token"
    valid_response_headers = { "Content-Type": "application/zip"}
    with requests_mock.Mocker() as m, mock.patch(
        "gen3.tools.download.drs_download.wts_get_token"
    ) as wts_get_token:
        m.get(
            f"https://{wts_hostname}/wts/token/?idp={idp}",
            json={"token": returned_idp_token},
        )
        m.post(
            "https://data.qdr.syr.edu/api/access/datafiles",
            headers = valid_response_headers,
            content = bytes(test_data, 'utf-8')           
        )
        wts_get_token.return_value = "some-idp-token"
        result = get_syracuse_qdr_files(
            wts_hostname = wts_hostname,
            auth = mock_auth,
            file_metadata_list = file_metadata_list,
            download_path = download_path
        )
        assert result == expected_status

        # failed downloads
        expected_status = {
            "QDR_file_02,QDR_file_03": DownloadStatus(
                filename="QDR_file_02,QDR_file_03", status="failed"
            )
        }
        with mock.patch(
            "heal.qdr_downloads.download_from_url"
        ) as mock_download_from_url:
            mock_download_from_url.return_value = False
            result = get_syracuse_qdr_files(
                wts_hostname = wts_hostname,
                auth = mock_auth,
                file_metadata_list = file_metadata_list,
                download_path = download_path
            )
            assert result == expected_status
