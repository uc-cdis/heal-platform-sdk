import os
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock

import pytest
import requests_mock
from gen3.tools.download.drs_download import DownloadStatus

from heal.mpd_downloads import (
    get_download_url_for_mpd,
    get_mpd_files,
    is_valid_mpd_file_metadata,
)
from heal.utils import get_filename, get_id


@pytest.fixture(scope="session")
def download_dir(tmpdir_factory):
    """Fixture for temporary download dir"""
    path = tmpdir_factory.mktemp("mpd_download_dir")
    return path


@pytest.mark.parametrize(
    "file_metadata",
    [
        (
            {
                "file_retriever": "MPD",
                "project_symbol": "Gould2",
            }
        ),
        (
            {
                "file_retriever": "MPD",
                "measure_id": 47115,
            }
        ),
        (
            {
                "file_retriever": "MPD",
                "measure_id": "2908",
            }
        ),
    ],
)
def test_is_valid_mpd_file_metadata(file_metadata: Dict):
    """Test valid MPD metadata"""
    assert is_valid_mpd_file_metadata(file_metadata)


def test_is_valid_mpd_file_metadata_failed():
    """Test invalid MPD metadata"""
    # missing keys
    file_metadata = {
        "file_retriever": "MPD",
        "description": "missing project_symbol or measure_id",
    }
    assert not is_valid_mpd_file_metadata(file_metadata)

    # not a dict
    file_metadata = ("file_metadata_is_not_a_dict",)
    assert not is_valid_mpd_file_metadata(file_metadata)


def test_get_id_fallback():
    """Test that get_id falls back to MPD-specific keys"""
    # get_id doesn't know about MPD keys, so it should return None
    # and the retriever should fall back to project_symbol or measure_id
    file_metadata = {
        "file_retriever": "MPD",
        "project_symbol": "Gould2",
    }
    # get_id doesn't know about project_symbol
    assert get_id(file_metadata) is None


def test_get_filename():
    """Test get_filename from valid metadata"""
    file_metadata = {
        "file_retriever": "MPD",
        "project_symbol": "Gould2",
        "filename": "custom_mpd_file.csv",
    }
    expected_filename = "custom_mpd_file.csv"
    assert get_filename(file_metadata) == expected_filename


@pytest.mark.parametrize(
    "file_metadata, expected",
    [
        (
            {
                "project_symbol": "Gould2",
            },
            "https://phenome.jax.org/api/projects/Gould2/dataset?csv=yes",
        ),
        (
            {
                "measure_id": 47115,
            },
            "https://phenome.jax.org/api/pheno/animalvals/47115?csv=yes",
        ),
        (
            {
                "measure_id": "2908",
            },
            "https://phenome.jax.org/api/pheno/animalvals/2908?csv=yes",
        ),
    ],
)
def test_get_download_url_for_mpd(file_metadata: Dict, expected: str):
    """Test get_download_url for valid MPD metadata"""
    assert get_download_url_for_mpd(file_metadata) == expected


def test_get_download_url_for_mpd_failed():
    """Test get_download_url for metadata missing required keys"""
    file_metadata = {"invalid": "metadata"}
    assert get_download_url_for_mpd(file_metadata) is None


def test_get_mpd_files_with_project_symbol(download_dir):
    """Test downloading MPD project data with project_symbol"""
    test_data = "project_id,strain,value\n1,C57BL/6J,10.5\n2,DBA/2J,12.3\n"
    test_project = "Gould2"

    file_metadata_list = [
        {
            "file_retriever": "MPD",
            "project_symbol": test_project,
        },
    ]

    # The object_id should be the project_symbol
    expected_status = {
        test_project: DownloadStatus(filename=f"{test_project}.csv", status="downloaded")
    }

    with requests_mock.Mocker() as m:
        # Mock the MPD API endpoint
        m.get(
            f"https://phenome.jax.org/api/projects/{test_project}/dataset?csv=yes",
            text=test_data,
        )

        mock_auth = MagicMock()
        mock_auth.get_access_token.return_value = "some_token"

        # Call the function to test
        result = get_mpd_files(
            wts_hostname="",
            auth=mock_auth,
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )

        # Check if the result matches the expected status
        assert result == expected_status

        # Verify the file was saved with default filename
        downloaded_file_path = Path(download_dir) / f"{test_project}.csv"
        assert downloaded_file_path.exists()
        assert downloaded_file_path.read_text() == test_data


def test_get_mpd_files_with_measure_id(download_dir):
    """Test downloading MPD phenotype measures with measure_id"""
    test_data = "animal_id,strain,sex,measurement\n123,C57BL/6J,M,8.5\n"
    test_measure_id = "2908"

    file_metadata_list = [
        {
            "file_retriever": "MPD",
            "measure_id": test_measure_id,
        },
    ]

    expected_status = {
        test_measure_id: DownloadStatus(
            filename=f"{test_measure_id}.csv", status="downloaded"
        )
    }

    with requests_mock.Mocker() as m:
        # Mock the MPD API endpoint
        m.get(
            f"https://phenome.jax.org/api/pheno/animalvals/{test_measure_id}?csv=yes",
            text=test_data,
        )

        mock_auth = MagicMock()

        result = get_mpd_files(
            wts_hostname="",
            auth=mock_auth,
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )

        assert result == expected_status

        downloaded_file_path = Path(download_dir) / f"{test_measure_id}.csv"
        assert downloaded_file_path.exists()
        assert downloaded_file_path.read_text() == test_data


def test_get_mpd_files_with_custom_filename(download_dir):
    """Test downloading MPD data with custom filename in metadata"""
    test_data = "project_id,strain,value\n1,C57BL/6J,10.5\n"
    test_project = "Gould2"
    custom_filename = "my_custom_mpd_data.csv"

    file_metadata_list = [
        {
            "file_retriever": "MPD",
            "project_symbol": test_project,
            "filename": custom_filename,
        },
    ]

    expected_status = {
        test_project: DownloadStatus(filename=custom_filename, status="downloaded")
    }

    with requests_mock.Mocker() as m:
        m.get(
            f"https://phenome.jax.org/api/projects/{test_project}/dataset?csv=yes",
            text=test_data,
        )

        mock_auth = MagicMock()

        result = get_mpd_files(
            wts_hostname="",
            auth=mock_auth,
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )

        assert result == expected_status

        # File should be saved with custom filename
        downloaded_file_path = Path(download_dir) / custom_filename
        assert downloaded_file_path.exists()
        assert downloaded_file_path.read_text() == test_data


def test_get_mpd_files_bad_input(download_dir):
    """Test get_mpd_files with invalid input"""
    mock_auth = MagicMock()

    # Missing required keys
    file_metadata_list = [
        {
            "file_retriever": "MPD",
            "invalid_key": "no_valid_id",
        },
    ]

    result = get_mpd_files(
        wts_hostname="",
        auth=mock_auth,
        file_metadata_list=file_metadata_list,
        download_path=download_dir,
    )
    assert result is None


def test_get_mpd_files_invalid_url(download_dir):
    """Test get_mpd_files when URL construction fails"""
    test_project = "TestProject"
    file_metadata_list = [
        {
            "file_retriever": "MPD",
            "project_symbol": test_project,
        },
    ]

    expected_status = {
        test_project: DownloadStatus(
            filename=f"{test_project}.csv", status="invalid url"
        )
    }

    mock_auth = MagicMock()

    # Mock get_download_url_for_mpd to return None
    from unittest import mock

    with mock.patch(
        "heal.mpd_downloads.get_download_url_for_mpd"
    ) as mock_get_download_url:
        mock_get_download_url.return_value = None

        result = get_mpd_files(
            wts_hostname="",
            auth=mock_auth,
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )
        assert result == expected_status


def test_get_mpd_files_failed_download(download_dir):
    """Test get_mpd_files when download fails"""
    test_project = "Gould2"
    file_metadata_list = [
        {
            "file_retriever": "MPD",
            "project_symbol": test_project,
        },
    ]

    expected_status = {
        test_project: DownloadStatus(filename=f"{test_project}.csv", status="failed")
    }

    mock_auth = MagicMock()

    with requests_mock.Mocker() as m:
        # Mock API to return error
        m.get(
            f"https://phenome.jax.org/api/projects/{test_project}/dataset?csv=yes",
            status_code=404,
        )

        result = get_mpd_files(
            wts_hostname="",
            auth=mock_auth,
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )

        assert result == expected_status


def test_get_mpd_files_invalid_download_path():
    """Test get_mpd_files with non-existent download path"""
    file_metadata_list = [
        {
            "file_retriever": "MPD",
            "project_symbol": "Gould2",
        },
    ]

    mock_auth = MagicMock()

    result = get_mpd_files(
        wts_hostname="",
        auth=mock_auth,
        file_metadata_list=file_metadata_list,
        download_path="/path/does/not/exist",
    )

    assert result is None


def test_get_mpd_files_multiple_files(download_dir):
    """Test downloading multiple MPD files in one call"""
    test_project_data = "project_id,strain,value\n1,C57BL/6J,10.5\n"
    test_measure_data = "animal_id,strain,sex,measurement\n123,C57BL/6J,M,8.5\n"
    test_project = "Gould2"
    test_measure = "2908"

    file_metadata_list = [
        {
            "file_retriever": "MPD",
            "project_symbol": test_project,
        },
        {
            "file_retriever": "MPD",
            "measure_id": test_measure,
        },
    ]

    expected_status = {
        test_project: DownloadStatus(
            filename=f"{test_project}.csv", status="downloaded"
        ),
        test_measure: DownloadStatus(filename=f"{test_measure}.csv", status="downloaded"),
    }

    with requests_mock.Mocker() as m:
        m.get(
            f"https://phenome.jax.org/api/projects/{test_project}/dataset?csv=yes",
            text=test_project_data,
        )
        m.get(
            f"https://phenome.jax.org/api/pheno/animalvals/{test_measure}?csv=yes",
            text=test_measure_data,
        )

        mock_auth = MagicMock()

        result = get_mpd_files(
            wts_hostname="",
            auth=mock_auth,
            file_metadata_list=file_metadata_list,
            download_path=download_dir,
        )

        assert result == expected_status

        # Verify both files exist
        project_file = Path(download_dir) / f"{test_project}.csv"
        measure_file = Path(download_dir) / f"{test_measure}.csv"
        assert project_file.exists()
        assert measure_file.exists()
        assert project_file.read_text() == test_project_data
        assert measure_file.read_text() == test_measure_data
