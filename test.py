#! /usr/bin/python3

import sys
from yajl import *
import sys

import logging
#logging.basicConfig(format="%(message)s", level=logging.DEBUG)
log = logging.getLogger()


def to_utf8(wrapped_method):
    def arg_utf8_converter(a, b, c):
        return wrapped_method(a, b, c.decode("utf8"))

    return arg_utf8_converter


class StructPointer:
    def __init__(self, initial_value):
        self.document = initial_value
        self.type = type(initial_value)
        self.pointer = None

    def set_value(self, value):
        if isinstance(self.document, dict):
            self.document[self.pointer] = value
        else:
            self.document.append(value)
            if self.pointer is None:
                self.pointer = 0
            else:
                self.pointer += 1

    def set_pointer(self, pointer):
        self.pointer = pointer

    def __str__(self):
        if self.pointer is None:
            return "<>"
        if isinstance(self.document, dict):
            return str(self.pointer)
        else:
            return str(self.pointer)


# Sample callbacks, which output some debug info
# these are examples to show off the yajl parser
class ContentHandler(YajlContentHandler):
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
        log.info("{} setting null".format(self._current_path))
        self._set_value(None)

    def yajl_boolean(self, ctx, boolVal):
       log.info("{} setting bool: {}".format(self._current_path,  boolVal))
       self._set_value(boolVal)

    def yajl_integer(self, ctx, integerVal):
        log.info("{} setting int: {}".format(self._current_path,  integerVal))
        self._set_value(integerVal)

    def yajl_double(self, ctx, doubleVal):
        log.info("{} setting float: {}".format(self._current_path,  doubleVal))
        self._set_value(doubleVal)

    @to_utf8
    def yajl_string(self, ctx, stringVal):
        log.info("{} setting string: {}".format(self._current_path, stringVal))
        self._set_value(stringVal)

    def yajl_start_map(self, ctx):
        new_map = {}
        self._set_value(new_map)
        self.document_pointer_stack.append(self.document_pointer)
        log.info("%s <= setting map", self._current_path_minus_one)
        self.document_pointer = StructPointer(new_map)

    @to_utf8
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
        new_pointer = self.document_pointer = StructPointer(new_array)

    def yajl_end_array(self, ctx):
        self.document_pointer = self.document_pointer_stack.pop()


handler = ContentHandler(to_stream=["packages"])

# Create the parser
parser = YajlParser(handler)
# Parse JSON from stdin
with open(sys.argv[1], "rb") as f:
    parser.parse(f=f)
