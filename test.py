#! /usr/bin/python3

"""
Read JSON as stream.
"""

import sys
import logging
import pprint

from yajl import YajlContentHandler, YajlParser


#logging.basicConfig(format="%(message)s", level=logging.DEBUG)
log = logging.getLogger()


def params_to_utf8(wrapped_method):
    """
    The arguments given by Yajl are byte strings, so convert them to UTF
    """
    def arg_utf8_converter(arg1, arg2, arg3):
        return wrapped_method(arg1, arg2, arg3.decode("utf8"))
    return arg_utf8_converter


class StructPointer:
    """
    Node in the stack of JSON nodes
    """
    def __init__(self, initial_value):
        self.document = initial_value
        self.type = type(initial_value)
        self.pointer = None

    def set_value(self, value):
        """
        Set the value of the currently processed field (given by pointer)
        """
        if isinstance(self.document, dict):
            self.document[self.pointer] = value
        else:
            self.document.append(value)
            if self.pointer is None:
                self.pointer = 0
            else:
                self.pointer += 1

    def set_pointer(self, pointer):
        """ Setup the currently filled-up key """
        self.pointer = pointer

    def __str__(self):
        if self.pointer is None:
            return "<>"
        if isinstance(self.document, dict):
            return str(self.pointer)
        return str(self.pointer)


class ContentHandler(YajlContentHandler):
    """
    Override the generic content handler
    """

    def __init__(self, to_stream):
        self.to_stream = to_stream
        self.full_output = None
        self.document = None

        # can point to None (root), array or dict
        self.document_pointer = None

        self.document_pointer_stack = []

    def _set_value(self, value):
        if self.document_pointer is None:
            self.document = value
        else:
            self.document_pointer.set_value(value)

    def _current_path_inner(self, minus_one=False):
        if not self.document_pointer:
            return "/"
        items = self.document_pointer_stack[1:] + [self.document_pointer]
        if minus_one:
            items = items[:-1]
        return "/" + "/".join([str(i) for i in items])

    @property
    def _current_path(self):
        return self._current_path_inner()

    @property
    def _current_path_minus_one(self):
        return self._current_path_inner(True)

    def yajl_null(self, ctx):
        log.info("%s setting null", self._current_path)
        self._set_value(None)

    def yajl_boolean(self, ctx, boolVal):
        log.info("%s setting bool: %s", self._current_path,  boolVal)
        self._set_value(boolVal)

    def yajl_integer(self, _, integer):
        """ store int """
        log.info("%s setting int: %s", self._current_path,  integer)
        self._set_value(integer)

    def yajl_double(self, _, double):
        """ store float """
        log.info("%s setting float: %s", self._current_path,  double)
        self._set_value(double)

    @params_to_utf8
    def yajl_string(self, ctx, stringVal):
        log.info("%s setting string: %s", self._current_path, stringVal)
        self._set_value(stringVal)

    def yajl_start_map(self, ctx):
        new_map = {}
        self._set_value(new_map)
        self.document_pointer_stack.append(self.document_pointer)
        log.info("%s <= setting map", self._current_path_minus_one)
        self.document_pointer = StructPointer(new_map)

    @params_to_utf8
    def yajl_map_key(self, ctx, stringVal):
        self.document_pointer.set_pointer(stringVal)
        log.info("%s (going to key '%s')", self._current_path_minus_one, stringVal)

    def yajl_end_map(self, ctx):
        log.info("%s end map", self._current_path_minus_one)
        self.document_pointer = self.document_pointer_stack.pop()

    def yajl_start_array(self, ctx):
        log.info("%s setting array", self._current_path)
        new_array = []
        self._set_value(new_array)
        self.document_pointer_stack.append(self.document_pointer)
        self.document_pointer = StructPointer(new_array)

    def yajl_end_array(self, ctx):
        self.document_pointer = self.document_pointer_stack.pop()


handler = ContentHandler(to_stream=["packages"])

# Create the parser
parser = YajlParser(handler)
# Parse JSON from stdin
with open(sys.argv[1], "rb") as f:
    parser.parse(f=f)

pprint.pprint(handler.document)
