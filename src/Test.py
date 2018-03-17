from __future__ import print_function

import io
import itertools
import os
import shutil
import sys

import httplib2
from apiclient import discovery
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from Util import *

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


# Todo add comments
def upload_file(service, file_path, file_name, mime_type, parent_id=None):
    file_metadata = {
        'name': [file_name],
        'parents': [parent_id]
    }
    media = MediaFileUpload(file_path,
                            mimetype=mime_type,
                            resumable=True)
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    print('File %s with id %s was uploaded' % (file_name, file.get('id')))


# Todo add comments
def download_file(service, file_metadata, destination_folder="/"):
    request = service.files().get_media(fileId=file_metadata[ID_FIELD_NAME])
    file_full_path = destination_folder + file_metadata[NAME_FIELD_NAME]
    fh = io.FileIO(file_full_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))

    return (file_full_path, file_metadata[MIME_TYPE_FIELD_NAME])


def load_service():
    """
    Initialize facade service for Drive API interactions.
    Selected driver version: V3
    Credentials are loaded from get_credentials() function
    """

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    return discovery.build('drive', 'v3', http=http)


# Todo add comments
def get_folder_metadata(service, folder_name):
    root_folder_predicate_list = [
        PredicateMetadata(MIME_TYPE_FIELD_NAME, "=", FOLDER_MIME_TYPE),
        PredicateMetadata(NAME_FIELD_NAME, "=", folder_name)
    ]
    return get_item_metadata_from_drive(service, root_folder_predicate_list)[0]


# Todo add comments and README file
def main():
    if len(sys.argv) < 4:
        print(
            "Not enough cmd arguments. You must specify 'LogoFileName.ext', "
            "'DestinationFolderName', 'PathToLocalTempFolder','SourceFolderName'(any amount).")

    # Todo extract loading of args to function
    system_args = iter(sys.argv)
    system_args.__next__()
    logo_file_name = system_args.__next__()
    destination_folder_name = "'%s'" % system_args.__next__()
    local_temp_folder = system_args.__next__()
    source_folder_name = []

    while True:
        try:
            source_folder_name.append(system_args.__next__())
        except StopIteration:
            break

    service = load_service()

    source_folder_metadata_list = []
    for folder_name in source_folder_name:
        source_folder_metadata_list.append(get_folder_metadata(service, "'%s'" % folder_name))
    destination_folder_metadata = get_folder_metadata(service, destination_folder_name)

    if not source_folder_metadata_list or not destination_folder_metadata:
        print('Illegal argument exception. Please check source and dest folder names')
        return

    if not os.path.exists(local_temp_folder):
        os.makedirs(local_temp_folder)

    child_documents = []
    for source_folder_metadata in source_folder_metadata_list:
        folder_id = source_folder_metadata[ID_FIELD_NAME]
        files_in_folder_predicate_list = [
            PredicateMetadata(TRASHED_FIELD_NAME, "!=", 'True'),
            PredicateMetadata("'%s'" % folder_id, "in", "parents")
        ]
        child_documents.append(get_item_metadata_from_drive(service, files_in_folder_predicate_list))

    flatten_child_documents = list(itertools.chain.from_iterable(child_documents))
    new_files_path = []
    for file_metadata in flatten_child_documents:
        new_files_path.append(download_file(service, file_metadata, local_temp_folder))

    logo_file_path = ""
    for file_metadata in new_files_path:
        if file_metadata[0].endswith(logo_file_name):
            logo_file_path = file_metadata[0]
            break
    if logo_file_path is "":
        print("Logo with name %s was not found" % logo_file_name)
        return

    # function that filter out videos. file_info_tuple[0] == full path like F:/some_folder/file.mp4
    # for file_info_tuple in new_files_path:
    #    if(file_info_tuple[1].startswith("video/")):
    #        print("Path to video: %s" % file_info_tuple[0])

    # Todo add here functions related to video
    # logo_file_path  contains full path to logo: F:/some_folder/file.mp4

    for file_info_tuple in new_files_path:
        if file_info_tuple[1].startswith("video/"):
            upload_file(service=service,
                        file_name=get_file_name_from_tuple(file_info_tuple),
                        file_path=file_info_tuple[0],
                        mime_type=file_info_tuple[1],
                        parent_id=destination_folder_metadata[ID_FIELD_NAME])
    if os.path.exists(local_temp_folder):
        shutil.rmtree(local_temp_folder, ignore_errors=True)


# Todo add comments
def get_item_metadata_from_drive(service, predicate_list, item_count=100):
    query = process_predicate_query(predicate_list)
    files_metadata = service.files() \
        .list(pageSize=item_count, q=query) \
        .execute() \
        .get(FILES_FIELD_NAME, [])
    print("Files found: %d" % len(files_metadata))
    return files_metadata


if __name__ == '__main__':
    main()
