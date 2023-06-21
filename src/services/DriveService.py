from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from src.config import Config
from src.utils.helpers import get_mine_type
from flask import current_app


class DriveService:
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self, token_path: str = None, credentials_path: str = None):
        try:
            self.token_path = os.path.join(
                current_app.static_folder, Config.TOKEN_PATH if not token_path else token_path)
            self.credentials_path = os.path.join(
                current_app.static_folder, Config.CREDENTIALS_PATH if not credentials_path else credentials_path)
        except Exception as ex:
            raise ex

    def check_authorization(self):
        """Check authorization to Google Drive.
        Returns : google.oauth2.credentials.Credentials | None
        """
        try:
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(
                    self.token_path, self.SCOPES)
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
            return creds
        except ValueError as ex:
            print("check_authorization [drive] failed: %s" % ex)
            return None
        except Exception as ex:
            print("check_authorization failed: %s" % ex)
            return None

    def upload_file(self, file_name: str, folder_id: str, new_file_name: str, mime_type: str = None):
        """Insert new file.
        Returns : Id's of the file uploaded

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            creds = self.check_authorization()
            if creds is None:
                return None
            service = build('drive', 'v3', credentials=creds)
            if not folder_id or not folder_id.strip():
                file_metadata = {"name": new_file_name}
            else:
                file_metadata = {"name": new_file_name, "parents": [folder_id]}
            media = MediaFileUpload(
                file_name, mimetype=mime_type, resumable=True)
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id, webViewLink, webContentLink, resourceKey, shared")
                .execute()
            )
            current_app.logger.info(
                f"upload_file successfully. {file}")
            return file

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f"An error occurred: {error}")
            return None
        except Exception as ex:
            print(f"upload failed: {ex}")
            return None

    def upload_file_with_conversion(self, current_file_name: str, current_mime_type: str, new_file_name: str, new_mime_type: str):
        """Upload file with conversion
        Returns: ID of the file uploaded

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            # create drive api client
            creds = self.check_authorization()
            if creds is None:
                return None

            service = build('drive', 'v3', credentials=creds)

            file_metadata = {
                'name': new_file_name,
                'mimeType': new_mime_type
            }
            media = MediaFileUpload(current_file_name, mimetype=current_mime_type,
                                    resumable=True)
            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, media_body=media,
                                          fields='id').execute()
            print(F'File with ID: "{file.get("id")}" has been uploaded.')

        except HttpError as error:
            print(F'An error occurred: {error}')
            file = None

        return file.get('id')

    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """ Create a folder and prints the folder ID
        Returns : Folder Id

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            creds = self.check_authorization()
            if creds is None:
                return None
            service = build('drive', 'v3', credentials=creds)
            file_metadata = {
                'name': folder_name,
                'mimeType': MimeType.google_folder,
            }
            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]

            folder = service.files().create(body=file_metadata, fields='id'
                                            ).execute()
            print(F'Folder ID: "{folder.get("id")}".')
            return folder

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f"create_folder - An error occurred: {error}")
            return None
        except Exception as ex:
            print(f"upload failed: {ex}")
            return None

    def search_folder(self, query: str):
        """Search folder in drive location with query string

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            # create drive api client
            creds = self.check_authorization()
            if creds is None:
                return None
            service = build('drive', 'v3', credentials=creds)
            files = []
            page_token = None
            while True:
                # pylint: disable=maybe-no-member
                response = service.files().list(q=query,
                                                # spaces=,
                                                fields='nextPageToken, '
                                                'files(id, name)',
                                                pageToken=page_token).execute()
                for file in response.get('files', []):
                    # Process change
                    print(F'Found file: {file.get("name")}, {file.get("id")}')
                files.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

        except HttpError as error:
            print(F'An error occurred: {error}')
            files = None
        return files

    def search_file(self, query: str):
        """Search file in drive location with query string

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            # create drive api client
            creds = self.check_authorization()
            if creds is None:
                return None
            service = build('drive', 'v3', credentials=creds)
            files = []
            page_token = None
            while True:
                # pylint: disable=maybe-no-member
                response = service.files().list(q=query,
                                                spaces='drive',
                                                fields='nextPageToken, '
                                                'files(id, name)',
                                                pageToken=page_token).execute()
                for file in response.get('files', []):
                    # Process change
                    print(F'Found file: {file.get("name")}, {file.get("id")}')
                files.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

        except HttpError as error:
            print(F'An error occurred: {error}')
            files = None

        return files


class MimeType:
    google_folder = 'application/vnd.google-apps.folder'
    google_file = 'application/vnd.google-apps.file'
    google_sheets = 'application/vnd.google-apps.spreadsheet'
    csv = 'text/csv'
    microsoft_word_docx = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    microsoft_xlsx = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    png = 'image/png'
    jpeg = 'image/jpeg'
    jpg = 'image/jpeg'
