import shutil
from io import StringIO

import sys

import os


class StringBuilder:
    """
    Wrapper for high performance string operations
    """
    _file_str = None

    def __init__(self):
        self._file_str = StringIO()

    def append(self, str):
        self._file_str.write(str)

    def __str__(self):
        return self._file_str.getvalue()


class PredicateMetadata:
    """
    Represent part of the query that used to determinate metadata from Drive API.
        predicate_name = name of the field we want to constraint
        predicate_operation = condition like =, != , is, etc...
        predicate_value = value of the constraint
    __str__ function returns string representation of fields that are separated by space in next order: name opr value.
    """
    predicate_name = None
    predicate_operation = None
    predicate_value = None

    def __init__(self, name, operation, value):
        self.predicate_name = name
        self.predicate_operation = operation
        self.predicate_value = value

    def __str__(self, *args, **kwargs):
        return "%s %s %s" % (self.predicate_name, self.predicate_operation, self.predicate_value)


def process_predicate_query(predicate_items, condition="and"):
    """
    Function processes PredicateMetadata list
    :param predicate_items: PredicateMetadata class items (List) will be used in query to DriveAPI
    :param condition: Logic operation like 'and', 'or', etc...
    :return: String representation of predicate value that can be used for requests from DriveAPI
    """
    if not predicate_items:
        return ""
    else:
        string_builder = StringBuilder()
        for predicate_item in predicate_items:
            cond = condition
            string_builder.append(("%s %s " % (predicate_item.__str__(), condition)))
    return string_builder.__str__()[: -(2 + len(condition))]


# Todo add comments
def get_file_name_from_tuple(file_metadata_tuple):
    return file_metadata_tuple[0].split("/")[-1]


def process_cmd_args():
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
    return logo_file_name, destination_folder_name, local_temp_folder, source_folder_name


def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def drop_folder(folder_name):
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name, ignore_errors=True)
