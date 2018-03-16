from __future__ import print_function
import httplib2
import io
import csv
import os
from apiclient import discovery
from googleapiclient.http import MediaIoBaseDownload ,MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    """Shows basic usage of the Google Drive API.

    Creates a Google Drive API service object and outputs the names and IDs
    for up to 10 files.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    results = service.files().list(
        pageSize=10, q="mimeType='application/vnd.google-apps.folder' and name = 'TestFolder'").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        folder_id = items[0]['id']
        childDocuments = service.files().list(
            pageSize=100,
            q=("trashed != True and %r in parents" % folder_id)

        ).execute()
        #print(childDocuments)

        for file in childDocuments.get('files', []):
            request = service.files().get_media(fileId=file['id'])
            fh = io.FileIO('F:/lol/'+file['name'], 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            print ("Download %d%%." % int(status.progress() * 100))

    file_metadata = {
        'name': 'lol.png',
        'parents': [folder_id]
     }
    media = MediaFileUpload('F:/lol.jpeg',
                            mimetype='image/jpeg',
                            resumable=True)
    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print ('File ID: %s' % file.get('id'))





if __name__ == '__main__':
    main()
