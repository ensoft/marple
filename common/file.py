# -------------------------------------------------------------
# file.py - generates unique file filenames
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Handles the naming of files.

Provides functions to either create a filename from a given name or to
generate a unique generic filename including the appropriate directory name.
Can also export them to disk.

"""

__all__ = ["find_unique_out_filename", "create_out_filename_generic",
           "create_unique_temp_filename", "import_out_filename",
           "export_out_filename"]

import logging
import os
import uuid

from . import paths

logger = logging.getLogger("common.file")
logger.setLevel(logging.DEBUG)


def find_unique_out_filename(module, ending=None):
    """
    Finds a (uniquely numbered) generic output filename that is not taken.

    :param module:
        The module after which the file should be named
    :param ending:
        Optional file extension

    :return:
        A generic filename that does not yet exist in the output
        directory.
    """

    filename = create_out_filename_generic(module, ending=ending)

    i = 1
    while os.path.isfile(filename):
        filename = create_out_filename_generic("collect", number=i,
                                               ending=".data")
        i += 1

    return filename


def create_out_filename_generic(module, number=None, ending=None):
    """
    Create a, not necessarily unique, generic output filename.

    Creates a generic output filename from the module, a number, and a file
        ending.

    :param module:
        The module after which the file should be named.
    :param number:
        Optional numbering of the file.
    :param ending:
        Optional ending of the file.
    :return:
        A generic filename including the module name, and the specified number
        and a file ending.
    """

    filename = "out-" + str(module)

    if number is not None:
        filename += str(number)
    if ending is not None:
        filename += str(ending)

    return filename


def create_unique_temp_filename():
    """Create a new unique generic filename for a file in the temp directory"""
    return paths.TMP_DIR + str(uuid.uuid4()) + ".tmp"


def export_out_filename(filename):
    """Saves the output filename in a file on disk"""
    with open(paths.VAR_DIR + "filename", "w") as fn:
        fn.write(filename)


def import_out_filename():
    """Gets the output filename from disk"""
    try:
        with open(paths.VAR_DIR + "filename", "r") as saved_filename:
            return saved_filename.readline()
    except FileNotFoundError:
        logger.debug("Unable to find filename helper file in %s"
                     , str(paths.VAR_DIR))
        raise
