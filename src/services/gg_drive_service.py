from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from src.config import Config

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]


'''
Upload file
    filePath: Đường dẫn/ file cần upload lên.
    folderId: Folder ở Gg drive
    credentialPath: Đường dẫn file chứa credential
    tokenPath: đường dẫn token
Returns: ID of the file uploaded
'''
def UploadFile(fileName, parentFolderId, tokenPath, credentialPath):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # folderId = '1hiroAqGX0xzd88rjtIv5B5paw0FggLpw'
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(tokenPath):
        creds = Credentials.from_authorized_user_file(tokenPath, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentialPath, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenPath, "w") as token:
            token.write(creds.to_json())
    try:
        service = build("drive", "v3", credentials=creds)

        # Call the Drive v3 API

        file_metadata = {"name": fileName, "parents": [parentFolderId]}
        media = MediaFileUpload(fileName, mimetype="image/jpg", resumable=True)
        # pylint: disable=maybe-no-member
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        print(f'File ID: {file.get("id")}')
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")

""" Create a folder and prints the folder ID
Returns : Folder Id 
"""
def CreateFolder(folderName, parentFolderId, tokenPath, credentialPath):
    """ Create a folder and prints the folder ID
    Returns : Folder Id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    
    creds = None
    # folderId = '1hiroAqGX0xzd88rjtIv5B5paw0FggLpw'
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(tokenPath):
        creds = Credentials.from_authorized_user_file(tokenPath, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentialPath, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenPath, "w") as token:
            token.write(creds.to_json())
    try:
        service = build("drive", "v3", credentials=creds)

        # Call the Drive v3 API
        
        file_metadata = {"name": folderName, "parents": [parentFolderId]}
        media = MediaFileUpload(folderName, mimetype="image/jpg", resumable=True)
        # pylint: disable=maybe-no-member
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        print(f'File ID: {file.get("id")}')
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")


