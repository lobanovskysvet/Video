from io import StringIO


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

#Todo add comments
def get_file_name_from_tuple(file_metadata_tuple):
    return file_metadata_tuple[0].split("/")[-1]
