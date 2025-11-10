"""
This module includes an external file retriever function intended to be called
by the external_files_download module in the Gen3-SDK.

The retriever function sends requests to the Mouse Phenome Database (MPD)
for downloading project data or phenotype measures.

The MPD documentation:
https://phenome.jax.org/about/api

Note:
MPD dynamically generates files (CSV or JSON) on request; there are no static files.
This retriever therefore downloads the on-demand CSV result for a given project or
measure ID, saves it locally, and returns DownloadStatus objects for consistency with
other external retrievers like Dryad, QDR, and Harvard Dataverse.
"""

from pathlib import Path
from typing import Dict, List
from cdislogging import get_logger
from gen3.tools.download.drs_download import DownloadStatus
from heal.utils import download_from_url, get_filename, get_id

MPD_API_BASE = "https://phenome.jax.org/api"

logger = get_logger("__name__", log_level="debug")


def get_mpd_files(
    wts_hostname: str, auth, file_metadata_list: List, download_path: str = "."
) -> Dict:
    """Retrieve data from the Mouse Phenome Database (MPD)."""
    if not Path(download_path).exists():
        logger.critical(f"Download path does not exist: {download_path}")
        return None

    completed = {}
    for file_metadata in file_metadata_list:
        object_id = get_id(file_metadata) or file_metadata.get("project_symbol") or file_metadata.get("measure_id")
        if not object_id:
            logger.warning(f"Invalid MPD metadata: {file_metadata}")
            continue

        filename = get_filename(file_metadata) or f"{object_id}.csv"
        completed[object_id] = DownloadStatus(filename=filename, status="pending")

        download_url = get_download_url_for_mpd(file_metadata)
        if not download_url:
            completed[object_id].status = "invalid url"
            continue

        logger.info(f"Downloading {object_id} from {download_url}")
        downloaded_file = download_from_url(
            api_url=download_url,
            headers=None,
            download_path=download_path,
            filename=filename,
        )

        if not downloaded_file:
            completed[object_id].status = "failed"
            continue

        completed[object_id].status = "downloaded"
        logger.info(f"Downloaded MPD data -> {downloaded_file}")

    return completed if completed else None


def get_download_url_for_mpd(file_metadata: Dict) -> str:
    """
    Build a download URL for the MPD API.

    Supported metadata keys:
      - project_symbol (e.g. 'Gould2')
      - measure_id (e.g. 47115)

    Returns:
        str: constructed API endpoint with CSV output
    """
    if "project_symbol" in file_metadata:
        proj = file_metadata["project_symbol"]
        return f"{MPD_API_BASE}/projects/{proj}/dataset?csv=yes"
    elif "measure_id" in file_metadata:
        meas = file_metadata["measure_id"]
        return f"{MPD_API_BASE}/pheno/animalvals/{meas}?csv=yes"
    else:
        logger.critical(f"Invalid MPD metadata keys: {file_metadata}")
        return None


def is_valid_mpd_file_metadata(file_metadata: Dict) -> bool:
    """
    Validate that file_metadata has an MPD identifier.
    Must contain 'project_symbol' or 'measure_id'.

    Args:
        file_metadata (Dict)

    Returns:
        bool
    """
    if not isinstance(file_metadata, dict):
        logger.critical(f"Invalid metadata (not dict): {file_metadata}")
        return False
    if "project_symbol" not in file_metadata and "measure_id" not in file_metadata:
        logger.critical(f"Invalid MPD metadata (missing ID): {file_metadata}")
        return False
    return True
