"""
This module includes an external file retriever function intended to be called
by the external_files_download module in the Gen3-SDK.

The retriever function sends requests to the Syracuse QDR API for downloading studies or files.

The QDR documentation describes how to download studies
https://guides.dataverse.org/en/latest/api/dataaccess.html#basic-download-by-dataset

and how to download files
https://guides.dataverse.org/en/latest/api/dataaccess.html#basic-file-access

In order to get an API token from the WTS server, users should have already
sent a request to
<WTS-SERVER>/oauth2/authorization_url?idp=externaldata-keycloak
and logged in to QDR after the redirect.

The WTS-SERVER is a Gen3 commons that has been configured to return
tokens for the 'idp' specified in the external_file_metadata.
"""


from pathlib import Path
from typing import Dict, List
from heal.utils import unpackage_object, get_id, download_from_url, get_idp_access_token

from cdislogging import get_logger
from gen3.tools.download.drs_download import DownloadStatus, wts_get_token

logger = get_logger("__name__", log_level="debug")


def get_syracuse_qdr_files(
    wts_hostname: str, auth, file_metadata_list: List, download_path: str = "."
) -> Dict:
    """
    Retrieves external data from the Syracuse QDR.

    Args:
        wts_hostname (str): hostname for commons with wts
        auth (Gen3Auth): auth for commons with wts
        file_metadata_list (List of Dict): list of studies or files
        download_path (str): path to download files and unpack

    Returns:
        Dict of download status
    """
    if not Path(download_path).exists():
        logger.critical(f"Download path does not exist: {download_path}")
        return None

    completed = {}
    logger.debug(f"Input file metadata list={file_metadata_list}")

    for file_metadata in file_metadata_list:
        id = get_id(file_metadata)
        if id is None:
            logger.warning(
                f"Could not find 'study_id' or 'file_id' in metadata {file_metadata}"
            )
            continue
        logger.info(f"ID = {id}")
        completed[id] = DownloadStatus(filename=id, status="pending")

        download_url = get_download_url_for_qdr(file_metadata)
        if download_url is None:
            logger.critical(f"Could not get download_url for {id}")
            completed[id].status = "invalid url"
            continue

        idp_access_token = get_idp_access_token(wts_hostname, auth, file_metadata)
        request_headers = get_request_headers(idp_access_token)
        if "Authorization" not in request_headers:
            logger.critical("WARNING Request headers do not include a bearer token.")

        logger.debug(f"Request headers = {request_headers}")

        logger.debug(f"Ready to send request to download_url: GET {download_url}")
        downloaded_file = download_from_url(
            api_url=download_url,
            headers=request_headers,
            download_path=download_path,
        )
        if downloaded_file is None:
            completed[id].status = "failed"
            continue

        if downloaded_file.endswith("zip"):
            # unpack if download is zip file
            try:
                logger.debug(f"Ready to unpack {downloaded_file}.")
                unpackage_object(filepath=downloaded_file)
            except Exception as e:
                logger.critical(f"{id} had an issue while being unpackaged: {e}")
                completed[id].status = "failed"

            completed[id].status = "downloaded"
            # remove the zip file
            Path(downloaded_file).unlink()
        else:
            completed[id].status = "downloaded"

    if not completed:
        return None
    return completed


def get_download_url_for_qdr(file_metadata: Dict) -> str:
    """
    Get the download url for Syracuse QDR.

    Args:
        file_metadata (Dict)

    Returns:
        url, None if there are errors
    """
    base_url = "https://data.qdr.syr.edu/api/access"
    if "use_qdr_staging" in file_metadata and bool(file_metadata["use_qdr_staging"]):
        base_url = "https://data.stage.qdr.org/api/access"

    if "study_id" in file_metadata:
        url = f"{base_url}/dataset/:persistentId/?persistentId={file_metadata.get('study_id')}"
    elif "file_id" in file_metadata:
        url = f"{base_url}/datafile/{file_metadata.get('file_id')}"
    else:
        url = None

    return url


def get_request_headers(idp_access_token: str) -> Dict:
    """
    Generate the request headers.

    Args:
        idp_access_token (str): QDR access token is included in request header as bearer token
        file_metadata (Dict)

    Returns:
        Dictionary of request headers
    """
    headers = {}
    if idp_access_token:
        headers["Authorization"] = f"Bearer {idp_access_token}"

    return headers


def is_valid_qdr_file_metadata(file_metadata: Dict) -> bool:
    """
    Check that the file_metadata has the required keys:
    'study_id' or 'file_id'.

    Args:
        file_metadata (Dict)

    Returns:
        True if valid file_metadata object.
    """
    if not isinstance(file_metadata, dict):
        logger.critical(f"Invalid metadata - item is not a dict: {file_metadata}")
        return False
    if "study_id" not in file_metadata and "file_id" not in file_metadata:
        logger.critical(f"Invalid metadata - missing required QDR keys {file_metadata}")
        return False
    if "study_id" in file_metadata and "file_id" in file_metadata:
        logger.critical(
            f"Invalid metadata - item has both 'study_id' and 'file_id': {file_metadata}"
        )
        return False
    return True
