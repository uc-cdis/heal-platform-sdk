import requests
import json
import os
import argparse


def query_dataverse_files(study_persistent_id):
    """
    Queries the Dataverse API to get all file metadata for a given study ID.
    """
    url = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={study_persistent_id}"
    response = requests.get(url)

    if response.status_code != 200:
        print("Error querying Dataverse API:", response.status_code, response.text)
        return None

    data = response.json()
    return data["data"]["latestVersion"]["files"]


def generate_external_file_metadata(files):
    """
    Generates external file metadata structure from the Dataverse API response.
    """
    external_file_metadata = []
    for file in files:
        file_metadata = {
            "external_oidc_idp": "dataverse-keycloak",
            "file_retriever": "Dataverse",
            "file_id": str(file["dataFile"]["id"]),
        }
        external_file_metadata.append(file_metadata)
    return external_file_metadata


def send_metadata_to_api(metadata, study_id):
    """
    Sends the metadata as a PUT request to MDS.
    """
    bearer_token = os.getenv("BEARER_TOKEN")
    if not bearer_token:
        print("Error: BEARER_TOKEN environment variable not set.")
        raise SystemExit(1)  # Exit with error code 1

    payload = {"external_file_metadata": metadata}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }
    target_api_url = f"https://qa-heal.planx-pla.net/mds/metadata/{study_id}?merge=true"

    response = requests.put(target_api_url, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        print(
            f"Successfully sent external_file_metadata to the MDS. Endpoint pinged {target_api_url}"
        )
        print(f"Metadata: {metadata}")
    else:
        print(f"Failed to send metadata. Status code: {response.status_code}")
        print(response.text)


# poetry run python heal/external_file_metadata_generator.py --persistent_id "doi:10.7910/DVN/PC5QR0" --study_id "HDP00249"
if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Process Dataverse extrenal file metadata and send it to MDS."
    )
    parser.add_argument(
        "--persistent_id", required=True, help="Persistent ID of the study on Dataverse"
    )
    parser.add_argument("--study_id", required=True, help="Study ID in MDS.")

    args = parser.parse_args()

    # Input Persistent ID and target API endpoint
    study_persistent_id = args.persistent_id
    study_id = args.study_id

    # Query Dataverse API
    print("Querying Dataverse API...")
    files = query_dataverse_files(study_persistent_id)
    if files is None:
        print("No files retrieved.")
    else:
        print(f"Retrieved {len(files)} files.")

        # Generate External File Metadata
        print("Generating external file metadata...")
        metadata = generate_external_file_metadata(files)
        print("Generated Metadata:", json.dumps(metadata, indent=4))

        # Send Metadata to MDS
        print("Sending metadata to MDS...")
        send_metadata_to_api(metadata, study_id)
        print("End of process.")
