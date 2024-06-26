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

import os

from pathlib import Path
import requests
from typing import Dict, List, Tuple
from urllib.parse import unquote
import zipfile

from cdislogging import get_logger
from gen3.auth import Gen3Auth
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
        if "X-Dataverse-key" not in request_headers:
            logger.critical("WARNING Request headers do not include 'X-Dataverse-key'.")

        logger.debug(f"Request headers = {request_headers}")

        logger.debug(f"Ready to send request to download_url: GET {download_url}")
        downloaded_file = download_from_url(
            qdr_url=download_url,
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


def download_from_url(
    qdr_url: str,
    headers=None,
    download_path: str = ".",
) -> str:
    """
    Retrieve data file (study_id or file_id) from url.
    Save the file based on the filename in the Content-Disposition response header.

    Args:
        qdr_url (str): url for QDR API
        headers (Dict): request headers
        download_path (str): path for saving downloaded zip file

    Returns:
        path to downloaded and renamed file.
    """
    try:
        response = requests.get(url=qdr_url, headers=headers, stream=True)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.critical(
            f"Was unable to get the download url: {qdr_url}. Timeout Error."
        )
        return None
    except requests.exceptions.HTTPError as exc:
        logger.critical(f"HTTPError in download {exc}")
        return None
    except requests.exceptions.ConnectionError as exc:
        logger.critical(f"ConnectionError in download {exc}")
        return None
    except Exception as exc:
        logger.critical(f"Error in download {exc}")
        return None
    logger.debug(f"Status code={response.status_code}")
    downloaded_file_name = get_filename_from_headers(response.headers)
    if downloaded_file_name is None:
        downloaded_file_name = qdr_url.split("/")[-1]
        logger.info(f"Using file name from id in url {downloaded_file_name}")

    if downloaded_file_name.endswith(
        "zip"
    ) and not "application/zip" in response.headers.get("Content-Type"):
        logger.critical("Response headers do not show zipfile content-type")

    total_downloaded = 0
    block_size = 8092  # 8K blocks might want to tune this.
    download_filename = f"{download_path}/{downloaded_file_name}"
    try:
        logger.info(f"Saving download as {download_filename}")
        with open(download_filename, "wb") as file:
            for data in response.iter_content(block_size):
                total_downloaded += len(data)
                file.write(data)
    except IOError as ex:
        logger.critical(f"IOError opening {download_filename} for writing: {ex}")
        return None

    if total_downloaded == 0:
        logger.critical("content-length is 0 and it should not be")
        return None
    logger.debug(f"Download size = {total_downloaded}")

    return download_filename


def get_download_url_for_qdr(file_metadata: Dict) -> str:
    """
    Get the download url for Syracuse QDR.

    Args:
        file_metadata (Dict)

    Returns:
        url, None if there are errors
    """
    base_url = "https://data.qdr.syr.edu/api/access"
    if "use_qdr_staging" in file_metadata and bool(file_metadata.use_qdr_staging):
        base_url = "https://data.stage.qdr.org/api/access"

    if "study_id" in file_metadata:
        url = f"{base_url}/dataset/:persistentId/?persistentId={file_metadata.get('study_id')}"
    elif "file_id" in file_metadata:
        url = f"{base_url}/datafile/{file_metadata.get('file_id')}"
    else:
        url = None

    return url


def get_filename_from_headers(headers: Dict) -> str:
    """
    Parse and decode downloaded file name from response headers

    Args:
        headers (dict): response headers

    Returns:
        file name as string
    """
    try:
        file_name = None
        content_response = headers.get("Content-Disposition").split(";")
        for part in content_response:
            # look for UTF-8 encoded file name
            if part.strip().startswith("filename*="):
                file_name = part.split("=", 1)[1].strip()
                if file_name.lower().startswith("utf-8''"):
                    file_name = file_name[7:]
                    file_name = unquote(file_name)
                    break
            elif part.strip().startswith("filename="):
                file_name = part.split("=", 1)[1].strip().strip('"')
                break
        if file_name is None:
            logger.info("Could not parse file name from headers")

    except Exception as e:
        logger.warning("Could not get file name from headers")

    return file_name


def get_idp_access_token(wts_hostname: str, auth: Gen3Auth, file_metadata: Dict) -> str:
    """Get an access token for QDR using a Gen3 commons WTS"""
    try:
        logger.debug("Ready to get auth token")
        wts_access_token = auth.get_access_token()
        logger.debug("Ready to get idp token")
        idp = file_metadata.get("external_oidc_idp")
        idp_access_token = wts_get_token(
            hostname=wts_hostname, idp=idp, access_token=wts_access_token
        )
    except Exception as e:
        logger.critical(f"Could not get token: {e}")
        return None

    return idp_access_token


def get_request_headers(idp_access_token: str) -> Dict:
    """
    Generate the request headers.

    Args:
        idp_access_token (str): QDR token is included in X-Dataverse-key header
        file_metadata (Dict)

    Returns:
        Dictionary of request headers
    """
    headers = {}
    if idp_access_token:
        headers["X-Dataverse-key"] = idp_access_token

    return headers


def get_id(file_metadata: Dict) -> str:
    """
    Parse out the object id from the metadata.

    Args:
        file_metadata (Dict)

    Returns:
        string
    """
    id_types = ["study_id", "file_id"]
    for id_type in id_types:
        if id_type in file_metadata:
            return file_metadata.get(id_type)

    return None


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


def unpackage_object(filepath: str):
    """Unpackage the downloaded zip file"""
    with zipfile.ZipFile(filepath, "r") as package:
        package.extractall(os.path.dirname(filepath))
