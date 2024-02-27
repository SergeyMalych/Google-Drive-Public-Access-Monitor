"""This script monitors a user’s Google Drive permissions.

It checks file permissions, and adjusts them if necessary.
It uses the Google Drive API to achieve this functionality.
"""

import os.path
import time
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.activity.readonly",
          "https://www.googleapis.com/auth/drive.metadata.readonly",
          "https://www.googleapis.com/auth/drive"]
DELTA = 1  # time in minutes to check for actions
PAGESIZE = 5  # number of items to monitor every DELTA


def authenticate():
    """Authenticates using OAuth 2.0 credentials.

    If credentials are not found, opens a browser window for user authorization.

    Returns:
          Credentials: Authenticated OAuth 2.0 credentials.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def getcreatedfiles(driveactivityservice, delta_minutes=2):
    """Retrieves recently created files using the Drive Activity API.

    Args:
        driveactivityservice: An authenticated Drive Activity API service.
        delta_minutes (int, optional): Time window in minutes to search for activity.
        Defaults to 2.

    Returns:
        list: List of recently created file names.
    """
    try:
        # Calculate the timestamp to search within the last delta_minutes
        timetosearch = datetime.utcnow() - timedelta(minutes=delta_minutes)
        # Convert to RFC 3339 format
        rfc3339_timestamp = timetosearch.isoformat() + "Z"

        # Define the query parameters
        query_body = {
            "pageSize": PAGESIZE,  # Set your desired page size
            "filter": f"time >= \"{rfc3339_timestamp}\" detail.action_detail_case:(CREATE)"
        }

        # Execute the query
        results = driveactivityservice.activity().query(body=query_body).execute()
        activities = results.get("activities", [])
        ret = []

        if not activities:
            print("[!] No new files found.")
        else:
            for activity in activities:
                item_id = activity["targets"][0]["driveItem"]["name"].split(
                    '/')[1]
                ret.append(item_id)

        return ret

    except Exception as e:
        print(f"[!] Error fetching activity: {e}")
        return None

    except HttpError as error:
        # TODO - Handleerrors from drive activity API.
        print(f"[!] An error occurred: {error}")
        return []


def get_file_metadata_by_id(driveservice, file_id):
    """Retrieves file metadata based on the given file ID using the Google Drive API.

    Args:
        driveservice: An authenticated Google Drive API service.
        file_id (str): The ID of the file to retrieve.

    Returns:
        dict or None: File metadata as a dictionary or None if an error occurs.
    """
    try:
        # Retrieve file metadata
        file_metadata = driveservice.files().get(fileId=file_id, fields='*').execute()
        print(f"[{file_id}] retreived file metadata")
        return file_metadata

    except Exception as e:
        print(f"Error fetching file: {e}")
        return None


def is_file_publicly_accessible(driveservice, file_id):
    """Checks if file is publicly accessible

    Args:
      driveservice: An authenticated Google Drive API service.
      file_id (str): The ID of the file.

    Returns:
      bool: True if file is publicly accessible.
    """
    file_metadata = get_file_metadata_by_id(driveservice, file_id)
    for permission in file_metadata["permissions"]:
        if "anyoneWithLink" in permission["id"]:
            return True
    return False


def is_file_in_public_folder(driveservice, file_id):
    """Checks if file parent folder is public

    Args:
      driveservice: An authenticated Google Drive API service.
      file_id (str): The ID of the file.

    Returns:
      bool: True if file parent folder is public.
    """
    try:
        # Retrieve file metadata
        file_metadata = driveservice.files().get(
            fileId=file_id, fields='parents').execute()
        parent_folders = file_metadata.get('parents', [])

        for parent_id in parent_folders:
            # Retrieve parent folder permissions
            permissions = driveservice.permissions().list(fileId=parent_id).execute()

            for permission in permissions.get('permissions', []):
                if permission.get('type') == 'anyone':
                    return True  # File is in a publicly shared folder

        return False  # File is not in a publicly shared folder

    except Exception as e:
        print(f"Error checking folder permissions: {e}")
        return None


def remove_permission(driveservice, file_id, permission_id="anyoneWithLink"):
    """Removes a specific permission from a file.

    Args:
      driveservice: An authenticated Google Drive API service.
      file_id (str): The ID of the file.
      permission_id (str): The ID of the permission to remove.

    Returns:
      bool: True if the permission was successfully removed, False otherwise.
    """
    try:
        # Execute the permission delete request
        driveservice.permissions().delete(
            fileId=file_id, permissionId=permission_id).execute()
        return True

    except Exception as e:
        print(f"[!] Error removing permission: {e}")
        return False


def main():
    creds = authenticate()
    driveactivityservice = build("driveactivity", "v2", credentials=creds)
    driveservice = build("drive", "v3", credentials=creds)

    while True:
        print("[*] started! Checking for new files...")
        new_items = getcreatedfiles(driveactivityservice, DELTA)
        if new_items:
            for item in new_items:
                print(f"[*] New item was found to be created with the id {item}")
                print(f"[{item}] Checking if file is publicly accessible...")
                isfilepubliclyaccessible = is_file_publicly_accessible(
                    driveservice, item)
                print(f"[{item}] is_file_publicly_accessible: " + 
                  "Yes" if isfilepubliclyaccessible else "No")
                print(f"[{item}] Checking if parent folder is publicly accessible")
                isfileinpublicfolder = is_file_in_public_folder(
                    driveservice, item)
                if isfileinpublicfolder:  # if file in public folder
                    print(f"[{item}] Removing public access...")
                    hasremovedpublicaccess = remove_permission(
                        driveservice, item)
                    print(f"[{item}] permissions removed: " + 
                      "Successfully" if hasremovedpublicaccess else "No")

        time.sleep(DELTA * 60)  # wait for DELTA (in seconds)


if __name__ == "__main__":
    main()
