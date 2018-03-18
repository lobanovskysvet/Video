from __future__ import print_function

import itertools
import threading

import DriveApiUtil
from Util import *


# Todo add comments and README file
def main():
    # Loads values passed from CMD
    logo_file_name, destination_folder_name, local_temp_folder_path, source_folder_name_list = process_cmd_args()

    # Initializes service for DriveApi interactions
    service = DriveApiUtil.load_service()

    # Gets source folders metadata list from remote Drive
    source_folder_metadata_list = _get_source_and_dest_metadata(service, source_folder_name_list)

    # Gets destination folder metadata from remote Drive
    destination_folder_metadata = DriveApiUtil.get_folder_metadata(service, destination_folder_name)

    # Validates source_folder and destination_folder
    if not source_folder_metadata_list or not destination_folder_metadata:
        print('Illegal argument exception. Please check source and dest folder names')
        return

    # Creates local temp folder
    create_folder(local_temp_folder_path)

    # Gets all file metadatas from remote Drive storage
    file_metadata_list = _get_all_files_metadata(service, source_folder_metadata_list)

    # Downloads files from Drive and return tuple(path_in_local_storage, mime_type).
    # Downloading is executed in the different threads.
    file_path_and_mime_type_tuple_list = download_file_and_get_path_and_mime_type_typle_list(file_metadata_list,
                                                                                             local_temp_folder_path)
    # Gets logo file path in the local storage
    logo_file_path = _get_logo_file_path(file_path_and_mime_type_tuple_list, logo_file_name)

    # Validates logo
    if logo_file_path is "":
        print("Logo with name %s was not found" % logo_file_name)
        return

    # Process video and send it to the remote Drive. Processing and uploading are executed in the different threads.
    process_and_send_video(file_path_and_mime_type_tuple_list, logo_file_path, destination_folder_metadata)

    # Removes local temp folder
    drop_folder(local_temp_folder_path)


def download_file_and_get_path_and_mime_type_typle_list(file_metadata_list, local_temp_folder_path):
    file_path_and_mime_type_tuple_list = []
    threads_to_join = []
    for file_metadata in file_metadata_list:
        thread = threading.Thread(target=_download_file_and_get_path_and_mime_type_typle_list,
                                  args=(file_metadata, local_temp_folder_path,
                                        file_path_and_mime_type_tuple_list))
        thread.start()
        threads_to_join.append(thread)

    for thread in threads_to_join:
        thread.join()
    return file_path_and_mime_type_tuple_list


def _download_file_and_get_path_and_mime_type_typle_list(file_metadata, local_temp_folder_path, result_list):
    result_list.append(
        DriveApiUtil.download_file(DriveApiUtil.load_service(), file_metadata, local_temp_folder_path))


def _get_logo_file_path(file_metadata_tuple_list, logo_file_name):
    for file_metadata in file_metadata_tuple_list:
        if file_metadata[0].endswith(logo_file_name) and file_metadata[1].startswith("image/"):
            return file_metadata[0]


def _get_source_and_dest_metadata(service, source_folder_name_list):
    source_folder_metadata_list = []
    for folder_name in source_folder_name_list:
        source_folder_metadata_list.append(DriveApiUtil.get_folder_metadata(service, "'%s'" % folder_name))
    return source_folder_metadata_list


def process_and_send_video(file_path_and_mime_type_tuple_list, logo_file_path, destination_folder_metadata):
    threads_to_join = []
    for file_info_tuple in file_path_and_mime_type_tuple_list:
        if file_info_tuple[1].startswith("video/"):
            thread = threading.Thread(target=_process_and_send_video,
                                      args=(logo_file_path, file_info_tuple,
                                            destination_folder_metadata[DriveApiUtil.ID_FIELD_NAME]))
            thread.start()
            threads_to_join.append(thread)

    for thread in threads_to_join:
        thread.join()


def _process_and_send_video(logo_file_path, video_info_tuple, destination_folder_id):
    _process_video(logo_file_path, video_info_tuple[0])
    service = DriveApiUtil.load_service()
    print("Video %s is uploading" % video_info_tuple[0])
    DriveApiUtil.upload_file(service=service,
                             file_name=get_file_name_from_tuple(video_info_tuple),
                             file_path=video_info_tuple[0],
                             mime_type=video_info_tuple[1],
                             parent_id=destination_folder_id)


def _process_video(logo_file_path, video_file_path):
    print("Video %s is processing" % video_file_path)
    # Todo add here functions related to video
    pass


def _get_all_files_metadata(service, source_folder_metadata_list):
    child_documents = []
    for source_folder_metadata in source_folder_metadata_list:
        folder_id = source_folder_metadata[DriveApiUtil.ID_FIELD_NAME]
        files_in_folder_predicate_list = [
            PredicateMetadata(DriveApiUtil.TRASHED_FIELD_NAME, "!=", 'True'),
            PredicateMetadata("'%s'" % folder_id, "in", "parents")
        ]
        child_documents.append(DriveApiUtil.get_item_metadata_from_drive(service, files_in_folder_predicate_list))

    return list(itertools.chain.from_iterable(child_documents))


if __name__ == '__main__':
    main()
