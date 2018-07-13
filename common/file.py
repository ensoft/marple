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
import os

from common import paths

__all__ = ["create_unique_temp_filename"]

import uuid


def create_out_filename(filename):
    """
    Creates a file filename in the out directory.

    Makes an output file filename from the output directory and the user
        specified filename. Raises an error if the filename already exists.

    """
    if os.path.isfile(paths.OUT_DIR + filename):
        raise FileExistsError

    return paths.OUT_DIR + filename


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

    i = 1  # put into function inside createfilename
    while os.path.isfile(paths.OUT_DIR + filename):
        filename = create_out_filename_generic("collect", number=i, ending=".data")
        i += 1

    return paths.OUT_DIR + filename


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
