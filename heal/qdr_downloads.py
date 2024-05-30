"""
This module sends requests to the Syracuse QDR API for downloading studies or files.

The QDR documentation describes how to download studies
https://https://guides.dataverse.org/en/latest/api/dataaccess.html#basic-download-by-dataset

and how to do bulk downloads of files
https://guides.dataverse.org/en/latest/api/dataaccess.html#multiple-file-bundle-download
"""

import os

from pathlib import Path
import zipfile
import requests
from typing import Dict, List, Tuple

from cdislogging import get_logger
from gen3.auth import Gen3Auth
from gen3.tools.download.drs_download import DownloadStatus, wts_get_token

logger = get_logger("__name__", log_level="debug")

def get_syracuse_qdr_files(
    wts_hostname: str,
    auth,
    file_metadata_list: List,
    download_path
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
    filepath = f"{download_path}/dataverse_files.zip"
    logger.debug(f"Input file metadata list={file_metadata_list}")

    # validate and parse the file_metadata list
    if not isinstance(file_metadata_list, list):
        logger.critical(f"Input file metadata list should be a list.")
        return None
    COLLATE_FILES = True
    file_metadata_list = check_ids_and_collate_file_ids(file_metadata_list, COLLATE_FILES)
    logger.debug(f"New file_metadata_list = {file_metadata_list}")

    for file_metadata in file_metadata_list:

        id = get_id(file_metadata)
        logger.info(f"ID = {id}")
        completed[id] = DownloadStatus(filename=id, status='pending')

        download_url = get_download_url_for_qdr(file_metadata)
        request_type = get_request_type(file_metadata)
        if request_type == None:
            logger.critical("Could not get valid request type from file_metadata")
            completed[id].status='invalid metadata'
            continue

        idp_access_token = get_idp_access_token(wts_hostname, auth, file_metadata)
        request_headers = get_request_headers(idp_access_token,file_metadata)
        if 'X-Dataverse-key' not in request_headers:
            logger.critical("WARNING Request headers do not include 'X-Dataverse-key'.")
        request_body = get_request_body(file_metadata)

        logger.debug(f"Request headers = {request_headers}")
        logger.debug(f"Request body = {request_body}")

        logger.debug(f"Ready to send request to download_url: {request_type} {download_url}")
        download_success = download_from_url(
            download_filename=filepath,
            request_type=request_type,
            qdr_url=download_url,
            headers=request_headers,
            body=request_body,
        )
        if download_success == False:
            completed[id].status = 'failed'
            continue

        # unpack the zip file
        try:
            logger.debug(f"Ready to unpack {filepath}.")
            unpackage_object(filepath=filepath)
        except Exception as e:
            logger.critical(
                f"{id} had an issue while being unpackaged: {e}"
            )
            completed[id].status = 'failed'

        completed[id].status = 'downloaded'
        # remove the zip file
        Path(filepath).unlink()

    if completed == {}:
        return None
    return completed


def check_ids_and_collate_file_ids(file_metadata_list: List, collate_file_ids: bool) -> List:
    """
    Check that items have 1 of the required keys 'study_id' or 'file_id'.

    Group the items with files into an item with a list of files

    Args:
        file_metadata_list (List): list of file_metadata items
        collate_file_ids (bool): if True then do file_id grouping

    Returns:
        List of file_metadata items.
    """
    new_metadata_list = []
    file_ids = []
    file_idp = None
    file_retriever = None

    for item in file_metadata_list:
        logger.debug(f"Checking item = {item}")
        if not is_valid_qdr_file_metadata(item):
            continue
        if "study_id" in item:
            new_metadata_list.append(item)
        elif "file_id" in item:
            if collate_file_ids:
                file_ids.append(item.get('file_id'))
                file_retriever = item.get('file_retriever')
                # TODO: start new list if any of these don't match previous item - though they should
                file_idp = item.get('external_oidc_idp')
            else:
                new_metadata_list.append(item)

    if collate_file_ids:
        if len(file_ids) > 0:
            file_ids_item = {
                "file_ids": ','.join(file_ids),
                "file_retriever": file_retriever,
                "external_oidc_idp": file_idp
            }
            new_metadata_list.append(file_ids_item)

    return new_metadata_list


def download_from_url(
    download_filename: str,
    request_type: str,
    qdr_url: str,
    headers = None,
    body: str = None,
) -> bool:
    """
    Retrieve data file (study or files) from url.

    Args:
        download_filename (str): path for saving downloaded zip file
        request_type (str): GET or POST
        qdr_url (str): url for QDR API
        headers (Dict): request headers
        body (str): fileIds for files, None for study

    Returns:
        bool
    """

    try:
        if request_type == "GET":
            response = requests.get(url=qdr_url, headers=headers)
        else:
            response = requests.post(url=qdr_url, headers=headers, data=body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        logger.critical(f"Download error {exc}")
        return False

    print(f"Status code={response.status_code}")
    print(f"File size={len(response.content)}")
    print(f"Content-disposition={response.headers.get('Content-disposition')}")
    print(f"Content-Type={response.headers.get('Content-Type')}")

    total_size_in_bytes = len(response.content)
    if total_size_in_bytes == 0:
        logger.critical(f"content-length is 0 and it should not be")
        return False

    if not 'application/zip' in response.headers.get('Content-Type'):
        logger.critical('Response headers do not show zipfile content-type')

    try:
        logger.debug(f"Saving zip file as {download_filename}")
        with open(download_filename, "wb") as file:
            # TODO: show progress bar
            # for data in response.iter_content(block_size):
            #     progress_bar.update(len(data))
            #     total_downloaded += len(data)
            #     file.write(data)
            file.write(response.content)
    except IOError as ex:
        logger.critical(f"IOError opening {download_filename} for writing: {ex}")
        return False

    return True


def get_download_url_for_qdr(file_metadata: Dict) -> str:
    """
    Get the download url for Syracuse QDR.

    Args:
        file_metadata (Dict)

    Returns:
        url, None if there are errors
    """
    base_url = "https://data.qdr.syr.edu/api/access"
    # base_url = "https://data.stage.qdr.org/api/access"

    if "study_id" in file_metadata:
        url = f"{base_url}/dataset/:persistentId/?persistentId={file_metadata.get('study_id')}"
    elif "file_id" in file_metadata:
        url = f"{base_url}/datafiles/{file_metadata.get('file_id')}"
    elif "file_ids" in file_metadata:
        url = f"{base_url}/datafiles"
    else:
        url = None

    return url

def get_idp_access_token(
    wts_hostname: str,
    auth: Gen3Auth,
    file_metadata: Dict
) -> str:
    """Get an access token for QDR using a Gen3 commons WTS"""
    try:
        print("Ready to get auth token")
        wts_access_token = auth.get_access_token()
        print("Ready to get idp token")
        idp = file_metadata.get("external_oidc_idp")
        idp_access_token = wts_get_token(
            hostname=wts_hostname, idp=idp, access_token=wts_access_token
        )
    except Exception as e:
        logger.critical(f"Could not get token: {e}")
        return None
    
    return idp_access_token


def get_request_headers(
    idp_access_token: str,
    file_metadata: Dict
) -> Dict:
    """
    Include dataverse header for files, None for studies

    Args:
        idp_access_token (str)
        file_metadata (Dict)

    Returns:
        Dictionary of request headers
    """
    headers = {}
    if "file_ids" in file_metadata:
        headers["Content-Type"] = "text/plain"
    if idp_access_token:
        headers["X-Dataverse-key"] = idp_access_token

    return headers


def get_request_body(file_metadata: Dict) -> str:
    """
    If id type = 'file_ids' then return
    fileIds=file1,file2,etc.
    else return None
    """
    if "file_ids" in file_metadata:
        return f"fileIds={file_metadata.get('file_ids')}"
    else:
        return None


def get_id(file_metadata: Dict) -> str:
    """
    Parse out the object id from the metadata.

    Args:
        file_metadata (Dict)

    Returns:
        string
    """
    id_types = ['study_id', 'file_id', 'file_ids']
    for id_type in id_types:
        if id_type in file_metadata:
            return file_metadata.get(id_type)

    return None


def is_valid_qdr_file_metadata(file_metadata: Dict) -> bool:
    """
    Check that the file_metadata has the required keys:
    "study_id" or "file_id".

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
        logger.critical(f"Invalid metadata - item has both 'study_id' and 'file_id': {file_metadata}")
        return False
    return True


def get_request_type(file_metadata: Dict) -> str:
    """
    Return "GET" for studies, "POST" for files.
    """

    if "study_id" in file_metadata or "file_id" in file_metadata:
        return "GET"
    elif "file_ids" in file_metadata:
        return "POST"
    else:
        return None


def unpackage_object(filepath: str):
    """Unpackage the downloaded zip file"""
    with zipfile.ZipFile(filepath, "r") as package:
        package.extractall(os.path.dirname(filepath))