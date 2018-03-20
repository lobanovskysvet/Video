from __future__ import print_function

import glob
import itertools
import threading
from shutil import copyfile

from PIL import Image
from moviepy.editor import *

import DriveApiUtil
from Util import *



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
    file_path_and_mime_type_tuple_list = download_file_and_get_path_and_mime_type_tuple_list(file_metadata_list,
                                                                                             local_temp_folder_path)
    # Gets logo file path in the local storage
    logo_file_path = _get_logo_file_path(file_path_and_mime_type_tuple_list, logo_file_name)

    # Validates logo
    if logo_file_path is "":
        print("Logo with name %s was not found" % logo_file_name)
        return

    # Process video and send it to the remote Drive. Processing and uploading are executed in the different threads.
    process_and_send_video(file_path_and_mime_type_tuple_list, logo_file_path, destination_folder_metadata,
                           local_temp_folder_path)

    # Removes local temp folder
    drop_folder(local_temp_folder_path)


def download_file_and_get_path_and_mime_type_tuple_list(file_metadata_list, local_temp_folder_path):
    """
        Function holds same business logic as the '_download_file_and_get_path_and_mime_type_tuple_list' func,
        but process it using multithreading.
        Returns the list of tuples (file_full_path, mimeType)
        :param file_metadata_list: list of file metadatas from remote Drive storage
        :param local_temp_folder_path: temporal path in local storage
        :return tuple(path_in_local_storage, mime_type)
    """
    file_path_and_mime_type_tuple_list = []
    threads_to_join = []
    for file_metadata in file_metadata_list:
        thread = threading.Thread(target=_download_file_and_get_path_and_mime_type_tuple_list,
                                  args=(file_metadata, local_temp_folder_path,
                                        file_path_and_mime_type_tuple_list))
        thread.start()
        threads_to_join.append(thread)

    for thread in threads_to_join:
        thread.join()
    return file_path_and_mime_type_tuple_list


def _download_file_and_get_path_and_mime_type_tuple_list(file_metadata, local_temp_folder_path, result_list):
    """
        Function  downloads files and get mime type of file metadatas from remote Drive storage
        :param file_metadata: file metadatas from remote Drive storage
        :param local_temp_folder_path: temporal path in local storage
        :param: result_list : list of
    """
    result_list.append(
        DriveApiUtil.download_file(DriveApiUtil.load_service(), file_metadata, local_temp_folder_path))


def _get_logo_file_path(file_metadata_tuple_list, logo_file_name):
    """
        Function  get logo's file path
        :param file_metadata_tuple_list: contains list of tuples with file metadata (file path, mime type)
        :param logo_file_name: name of logo file
        :return the full path of the logo file
    """
    for file_metadata in file_metadata_tuple_list:
        if file_metadata[0].endswith(logo_file_name) and file_metadata[1].startswith("image/"):
            return file_metadata[0]


def _get_source_and_dest_metadata(service, source_folder_name_list):
    """
        Function  gets source folders metadata list from remote Drive
        :param service: facade for Drive API interactions
        :param source_folder_name_list : list of names of source folder names
        :return list of metadata of source folders
    """
    source_folder_metadata_list = []
    for folder_name in source_folder_name_list:
        source_folder_metadata_list.append(DriveApiUtil.get_folder_metadata(service, "'%s'" % folder_name))
    return source_folder_metadata_list


def get_video_related_logo_file_path(logo_file_path, video_name, local_folder_path):
    """
        Function  creates the file name associated with the video
        :param logo_file_path: logo name with extension
        :param video_name: name of the video
        :param local_folder_path: path to local temp folder
        :return new name for temp logo that can be used for creating local copy of the file
    """
    return "%s%s%s" % (
        local_folder_path,  #
        video_name.rsplit('/', 1)[-1],
        logo_file_path.rsplit('/', 1)[-1]
    )


def process_and_send_video(file_path_and_mime_type_tuple_list, logo_file_path, destination_folder_metadata,
                           local_folder_path):
    """
        Function holds same business logic as the '_process_and_send_video' func,
        but process it using new thread for each video. Creates copy of the logo for each thread for non-blocking I/O
        :param file_path_and_mime_type_tuple_list : list of the items,
            that correspond to the downloaded files from the remote Drive and their mimeTypes
        :param logo_file_path :the full path of the logo file
        :param destination_folder_metadata: metadata of destination folder
        :param local_folder_path: path to the local temp folder
    """

    threads_to_join = []

    for file_info_tuple in file_path_and_mime_type_tuple_list:
        if file_info_tuple[1].startswith("video/"):
            video_related_logo_copy_path = get_video_related_logo_file_path(
                logo_file_path,
                file_info_tuple[0],
                local_folder_path)

            # Creating local copy of the logo to provide non-blocking interactions with I/O streams
            copyfile(logo_file_path, video_related_logo_copy_path)
            thread = threading.Thread(target=_process_and_send_video,
                                      args=(video_related_logo_copy_path, file_info_tuple,
                                            destination_folder_metadata[DriveApiUtil.ID_FIELD_NAME]))
            thread.start()
            threads_to_join.append(thread)

    for thread in threads_to_join:
        thread.join()


def _process_and_send_video(logo_file_path, video_info_tuple, destination_folder_id):
    """
        Function process the video with a logo image and uploads it to the remote Drive
        :param logo_file_path : the full path of the logo file
        :param video_info_tuple : tuple (full path to the video, mimeType)
        :param destination_folder_id: id of destination folder

    """
    _process_video(logo_file_path, video_info_tuple[0])
    service = DriveApiUtil.load_service()
    print("Video %s is uploading" % video_info_tuple[0])
    DriveApiUtil.upload_file(service=service,
                             file_name=get_file_name_from_tuple(video_info_tuple),
                             file_path=video_info_tuple[0],
                             mime_type=video_info_tuple[1],
                             parent_id=destination_folder_id)


def scale(w, h, x, y, maximum=True):
    """
        Function calculates size of the image while keeping the aspect ratio
        :param w : image width
        :param h : image height
        :param x : the size of the box into which an image is inserted
        :param y : the size of the box into which an image is inserted
        :return new size of an image (width,height)
    """
    nw = y * w / h
    nh = x * h / w
    if maximum ^ (nw >= x):
        return nw or 1, y
    return x, nh or 1


def get_centered_coordinates(images, size):
    """
        Function gets the coordinates of the transformed image if the image were centered inside of square
        :param images :  the full path of the logo file
        :param size : the size of the box into which an image is inserted (width,height)
        :return  the coordinates of the transformed image
    """

    for im in images:
        new_image = Image.open(im)
        scale_data = new_image.size[0], new_image.size[1], size[0], size[1], True

        scale_data = scale(*scale_data)

        new_image.thumbnail(scale_data)
        x_position = (size[0] - new_image.size[0]) / 2
        y_position = (size[1] - new_image.size[1]) / 2

    return int(new_image.size[0] + x_position), int(new_image.size[1] + y_position)


def _get_prepared_image_for_video(name_logo, width, height, start_time, end_time):
    """
        Function resizes logo to fit in square container 1:1 ratio that fits in bottom right of the screen  in the video
        if logos are rectangular,it will be centered inside of square.
        :param name_logo : the full path of the logo file
        :param width : video width
        :param height : video height
        :param start_time :
        :param end_time :
        :return  transformed image that was fit in the square and ready for video processing
    """
    images = glob.glob(name_logo)
    size = (300, 300)
    logo = ImageClip(name_logo)
    w, h = logo.size
    if w == h:
        new_logo = logo.set_position(("right", "bottom")).set_start(start_time).set_duration(end_time).resize(0.2)
    else:
        x, y = get_centered_coordinates(images, size)
        new_logo = logo.set_position((width - x, height - y)).set_start(start_time).set_duration(end_time).resize(
            scale(w, h, size[0], size[1]))
    return new_logo


def _process_video(logo_file_path, video_file_path):
    """
        Function added transformed logo in bottom right of the screen  in the video
        :param logo_file_path: the full path of the logo file
        :param video_file_path : the full path of the video file

    """
    print("Video %s is processing" % video_file_path)

    clip = VideoFileClip(video_file_path)
    start_time = 0
    end_time = 10
    width, height = clip.size
    name = logo_file_path
    prepared_logo = _get_prepared_image_for_video(name, width, height, start_time, end_time)
    clip = CompositeVideoClip([clip, prepared_logo])
    clip.write_videofile(video_file_path, fps=24, verbose=False, progress_bar=False)


def _get_all_files_metadata(service, source_folder_metadata_list):
    """
        Function gets files metadata at specific folders from remote Drive
        :param service: facade for Drive API interactions
        :param source_folder_metadata_list: source folders metadata list
        :return List of the files metadata that were found in specified folders
    """
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
