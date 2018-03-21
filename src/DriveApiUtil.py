from __future__ import print_function

import io
import os
from argparse import Namespace

import httplib2
from apiclient import discovery
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from Util import PredicateMetadata, process_predicate_query

TRASHED_FIELD_NAME = "trashed"

FILES_FIELD_NAME = 'files'

NAME_FIELD_NAME = "name"

MIME_TYPE_FIELD_NAME = "mimeType"

ID_FIELD_NAME = 'id'

FOLDER_MIME_TYPE = "'application/vnd.google-apps.folder'"

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'


def get_item_metadata_from_drive(service, predicate_list, item_count=100):
    """
    Reads items metadata from remote Drive
    :param service: facade for Drive API interactions
    :param predicate_list: list of the restrictions which would be applied to the query (part of the Drive API).
     Query provides availability to filter out result set of the items from remote Drive
    :param item_count: max count of the items that we expect in the one result set
    :return: file metadata, that contains such fields: mime type, file name, file id, etc...
    """
    query = process_predicate_query(predicate_list)
    files_metadata = service.files() \
        .list(pageSize=item_count, q=query) \
        .execute() \
        .get(FILES_FIELD_NAME, [])
    return files_metadata


def get_folder_metadata(service, folder_name):
    """
    Reads specific folder metadata
    :param service: facade for Drive API interactions
    :param folder_name: name of the folder, that would be searched in the remote Drive
    :return: folder metadata
    """
    root_folder_predicate_list = [
        PredicateMetadata(MIME_TYPE_FIELD_NAME, "=", FOLDER_MIME_TYPE),
        PredicateMetadata(NAME_FIELD_NAME, "=", folder_name)
    ]
    return get_item_metadata_from_drive(service, root_folder_predicate_list)[0]


def upload_file(service, file_path, file_name, mime_type, parent_id=None):
    """
    Uploads file to the remote storage with specific parent folder, mime type and name
    :param service: facade for Drive API interactions
    :param file_path: path to the file on the local storage that would be uploaded
    :param file_name: name with which file would be saved on the remote Drive
    :param mime_type: mime type of the file (video/mp4, image/jpg, etc.)
    :param parent_id: id of the parent folder
    """
    file_metadata = {
        'name': [file_name],
        'parents': [parent_id]
    }
    media = MediaFileUpload(file_path,
                            mimetype=mime_type,
                            resumable=True)
    service.files().create(body=file_metadata,
                           media_body=media,
                           fields='id').execute()
    print('File %s was uploaded' % file_name)


def download_file(service, file_metadata, destination_folder="/"):
    """
    Downloads specific file from remote Drive. File specification is stored in the file_metadata
    :param service: facade for Drive API interactions
    :param file_metadata: holds information about particular item from the remote Drive
    :param destination_folder: local folder that would be used as the tepm storage
    :return: tuple(full file path on the local storage, mime type)
    """
    request = service.files().get_media(fileId=file_metadata[ID_FIELD_NAME])
    file_full_path = destination_folder + file_metadata[NAME_FIELD_NAME]
    fh = io.FileIO(file_full_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("File %s  --> %d%%." % (file_metadata[NAME_FIELD_NAME], int(status.progress() * 100)))

    return file_full_path, file_metadata[MIME_TYPE_FIELD_NAME]


def load_service():
    """
    Initialize facade service for Drive API interactions.
    Selected driver version: V3
    Credentials are loaded from get_credentials() function
    """
    credentials = _get_credentials()
    http = credentials.authorize(httplib2.Http())
    return discovery.build('drive', 'v3', http=http)


def _get_credentials():
    """
    Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    :return: credentials, the obtained credential.
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
        flags = Namespace(auth_host_name='localhost', auth_host_port=[8090,8080], logging_level='ERROR',noauth_local_webserver=False)
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials
