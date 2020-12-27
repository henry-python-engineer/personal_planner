from __future__ import print_function
import pickle
import os.path
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload


def get_creds():
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/drive']  # deleted "".metadata.readonly" from guide
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('config/token.pickle'):  # from guide, add config/
        with open('config/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'config/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('config/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def get_service_client(creds):
    service = build('drive', 'v3', credentials=creds)
    return service


def get_folder_id(service, folder_name):
    folder_id_result = service.files().list(
        q="trashed=false and mimeType='application/vnd.google-apps.folder' and name = '%s'"%folder_name,
        pageSize=10,
        fields="nextPageToken, files(id, name)"
    ).execute().get('files', [])
    folder_id = folder_id_result[0].get('id')
    return folder_id


def get_file_id(service, folder_name, file_name):
    folder_id = get_folder_id(service, folder_name)
    file_id_result = service.files().list(
        q="trashed=false and '{}' in parents and name = '{}'".format(folder_id, file_name),
        pageSize=10,
        fields="nextPageToken, files(id, name)"
    ).execute().get('files', [])
    file_id = file_id_result[0].get('id')
    return file_id


def get_file_list(service, **kwargs):
    folder_name = kwargs.get("folder_name","")
    folder_id = get_folder_id(service, folder_name)
    results = service.files().list(
        q="'%s' in parents and trashed=false"%folder_id,
        pageSize=10,
        fields="nextPageToken, files(id, name, size)"  # * gives us entire items
    ).execute().get('files', [])
    return results


def upload_file(service, **kwargs):
    local_directory = kwargs.get("local_directory", "data")
    local_file_name = kwargs.get("local_file_name", "")
    remote_directory = kwargs.get("remote_directory", "")
    remote_file_name = kwargs.get("remote_file_name", "unnamed.csv")
    remote_directory_id = get_folder_id(service, remote_directory)
    file_metadata = {
        'name': remote_file_name,
        'parents': [remote_directory_id],
    }
    media = MediaFileUpload(
        '{}/{}'.format(local_directory, local_file_name),
        mimetype="text/csv",
        resumable=True,
    )
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
    ).execute()


def download_file(service, **kwargs):
    remote_directory = kwargs.get("remote_directory", "")
    remote_file_name = kwargs.get("remote_file_name", "")
    local_directory = kwargs.get("local_directory", "")
    local_file_name = kwargs.get("local_file_name", "")
    file_id = get_file_id(service, remote_directory, remote_file_name)
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO('{}/{}'.format(local_directory, local_file_name), 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))


def main():
    creds = get_creds()
    service = get_service_client(creds)
    file_list = get_file_list(service, folder_name="test1")
    upload_file(service, local_directory='data', local_file_name='upload_test.csv', remote_directory='test1', remote_file_name='new_name1.csv')
    download_file(service, local_directory='data', local_file_name='download_test.csv', remote_directory='test1', remote_file_name='new_name1.csv')


if __name__ == '__main__':
    main()