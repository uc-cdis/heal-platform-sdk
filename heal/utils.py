import os
import requests
from typing import Dict
from urllib.parse import unquote
import zipfile
from cdislogging import get_logger
from gen3.auth import Gen3Auth
from gen3.tools.download.drs_download import wts_get_token

logger = get_logger("__name__", log_level="debug")


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


def unpackage_object(filepath: str):
    """Unpackage the downloaded zip file"""
    with zipfile.ZipFile(filepath, "r") as package:
        package.extractall(os.path.dirname(filepath))


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


def download_from_url(
    api_url: str,
    headers=None,
    download_path: str = ".",
) -> str:
    """
    Retrieve data file (study_id or file_id) from url.
    Save the file based on the filename in the Content-Disposition response header.

    Args:
        api_url (str): url for QDR or Harvard API
        headers (Dict): request headers
        download_path (str): path for saving downloaded zip file

    Returns:
        path to downloaded and renamed file.
    """
    try:
        response = requests.get(url=api_url, headers=headers, stream=True)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.critical(
            f"Was unable to get the download url: {api_url}. Timeout Error."
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
        downloaded_file_name = api_url.split("/")[-1]
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
