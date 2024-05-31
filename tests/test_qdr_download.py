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
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            },
            "GET",
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
            "GET",
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_ids": "QDR_file_01, QDR_file_02",
            },
            "POST",
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
def test_get_request_type(file_metadata: Dict, expected: str):
    assert get_request_type(file_metadata) == expected


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
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_ids": "QDR_file_01,QDR_file_02",
            },
            "QDR_file_01,QDR_file_02",
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
                },
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
                },
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
                },
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
                },
            ],
        ),
    ],
)
def test_check_ids_and_collate_file_ids(
    file_metadata: Dict, collate_file_ids: bool, expected: Dict
):
    assert check_ids_and_collate_file_ids(file_metadata, collate_file_ids) == expected


def test_get_request_body():
    # include 'file_ids' key
    file_metadata = {
        "external_oidc_idp": "test-external-idp",
        "file_retriever": "QDR",
        "file_ids": "QDR_file_01,QDR_file_02",
    }
    assert get_request_body(file_metadata) == "fileIds=QDR_file_01,QDR_file_02"


@pytest.mark.parametrize(
    "file_metadata",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
            },
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "file_id": "QDR_file_02",
            },
        ),
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
            },
        ),
    ],
)
def test_get_request_body_no_file_ids_key(file_metadata: Dict):
    # file_metadata does not have 'file_ids' key
    assert get_request_body(file_metadata) == None


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


def test_get_request_headers_for_file_ids():
    mock_idp_token = "some-idp-token"

    # with file_ids - includes the 'Content-Type' header
    file_metadata = {
        "external_oidc_idp": "test-external-idp",
        "file_retriever": "QDR",
        "file_ids": "QDR_file_01,QDR_file_02",
    }
    expected_headers = {"Content-Type": "text/plain", "X-Dataverse-key": mock_idp_token}
    assert (
        get_request_headers(
            idp_access_token=mock_idp_token, file_metadata=file_metadata
        )
        == expected_headers
    )

    # missing idp token - no 'X-Dataverse-key' header
    expected_headers = {
        "Content-Type": "text/plain",
    }
    assert (
        get_request_headers(idp_access_token=None, file_metadata=file_metadata)
        == expected_headers
    )


def test_get_request_headers_for_study_or_file():
    mock_idp_token = "some-idp-token"

    # without file_ids - just the X-Dataverse-key
    file_metadata = {
        "external_oidc_idp": "test-external-idp",
        "file_retriever": "QDR",
        "study_id": "QDR_study_01",
    }
    expected_headers = {"X-Dataverse-key": mock_idp_token}
    assert (
        get_request_headers(
            idp_access_token=mock_idp_token, file_metadata=file_metadata
        )
        == expected_headers
    )

    # missing idp token - empty headers
    expected_headers = {
        "Content-Type": "text/plain",
    }
    assert get_request_headers(idp_access_token=None, file_metadata=file_metadata) == {}


# TODO: split into 2 tests valid and failed
@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "external_oidc_idp": "test-external-idp",
                "file_retriever": "QDR",
                "study_id": "QDR_study_01",
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


def test_download_from_url(download_dir):
    request_headers = {"X-Dataverse-key": "some-idp-token"}
    valid_response_headers = {"Content-Type": "application/zip"}
    test_data = "foo"
    download_filename = f"{download_dir}/dataverse_files.zip"
    if os.path.exists(download_filename):
        Path(download_filename).unlink()

    with requests_mock.Mocker() as m:
        # get study_id
        qdr_url = "https://data.qdr.test.edu/api/access/:persistentId/?persistentId=QDR_study_01"
        m.get(
            qdr_url, headers=valid_response_headers, content=bytes(test_data, "utf-8")
        )
        result = download_from_url(
            download_filename=download_filename,
            request_type="GET",
            qdr_url=qdr_url,
            headers=request_headers,
            body=None,
        )
        assert result == True
        assert os.path.exists(download_filename)
        with open(download_filename, "r") as f:
            assert f.read() == test_data
        Path(download_filename).unlink()

        # post file_ids
        qdr_url = "https://data.qdr.test.edu/api/access/datafiles"
        m.post(
            qdr_url, headers=valid_response_headers, content=bytes(test_data, "utf-8")
        )
        result = download_from_url(
            download_filename=download_filename,
            request_type="POST",
            qdr_url=qdr_url,
            headers=request_headers,
            body="fileIds=QDR_file_01,QDR_file_02",
        )
        assert result == True
        assert os.path.exists(download_filename)
        with open(download_filename, "r") as f:
            assert f.read() == test_data
        Path(download_filename).unlink()


def test_download_from_url_failures(download_dir):
    request_headers = {"X-Dataverse-key": "some-idp-token"}
    valid_response_headers = {"Content-Type": "application/zip"}
    test_data = "foo"
    download_filename = f"{download_dir}/dataverse_files.zip"
    if os.path.exists(download_filename):
        Path(download_filename).unlink()

    with requests_mock.Mocker() as m:
        # bad url
        m.post(
            "https://bad_url",
            headers=valid_response_headers,
            content=bytes(test_data, "utf-8"),
        )
        result = download_from_url(
            download_filename="/path/does/not/exist",
            request_type="POST",
            qdr_url="https://bad_url",
            headers=request_headers,
            body="fileIds=QDR_file_01,QDR_file_02",
        )
        assert result == False
        assert not os.path.exists(download_filename)

        qdr_url = "https://data.qdr.test.edu/api/access/datafiles"

        # bad download path
        m.post(
            qdr_url, headers=valid_response_headers, content=bytes(test_data, "utf-8")
        )
        result = download_from_url(
            download_filename="/path/does/not/exist",
            request_type="POST",
            qdr_url=qdr_url,
            headers=request_headers,
            body="fileIds=QDR_file_01,QDR_file_02",
        )
        assert result == False
        assert not os.path.exists(download_filename)

        # zero size response
        m.post(qdr_url, headers=valid_response_headers, content=bytes())
        result = download_from_url(
            download_filename=download_filename,
            request_type="POST",
            qdr_url=qdr_url,
            headers=request_headers,
            body="fileIds=QDR_file_01,QDR_file_02",
        )
        assert result == False
        assert (os.path.getsize(download_filename)) == 0
        Path(download_filename).unlink()


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


# TODO: add test for bad download path


def test_get_syracuse_qdr_files(wts_hostname, download_dir):
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
        },
    ]
    expected_status = {
        "QDR_file_02,QDR_file_03": DownloadStatus(
            filename="QDR_file_02,QDR_file_03", status="downloaded"
        )
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
        m.post(
            "https://data.qdr.syr.edu/api/access/datafiles",
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


def test_get_syracuse_qdr_files_failed_download(wts_hostname, download_dir):
    idp = "test-external-idp"
    test_data = "foo"

    # valid input
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
        },
    ]

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
        # failed downloads
        m.post(
            "https://data.qdr.syr.edu/api/access/datafiles",
            headers=valid_response_headers,
            content=bytes(test_data, "utf-8"),
        )
        with mock.patch(
            "heal.qdr_downloads.download_from_url"
        ) as mock_download_from_url:
            mock_download_from_url.return_value = False
            expected_status = {
                "QDR_file_02,QDR_file_03": DownloadStatus(
                    filename="QDR_file_02,QDR_file_03", status="failed"
                )
            }
            result = get_syracuse_qdr_files(
                wts_hostname=wts_hostname,
                auth=mock_auth,
                file_metadata_list=file_metadata_list,
                download_path=download_dir,
            )
            assert result == expected_status
