# -------------------------------------------------------------
# file.py - generates unique file names
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Generates unique file names

Provides functions to generate a filename if no name was provided by the user.

"""

__all__ = ["create_temp_name"]

import uuid


def create_temp_name():
    """Create a new unique generic name for a file"""
    return str(uuid.uuid4()) + ".tmp"


def create_out_name(module, number=None, ending=None):
    """Create a generic output name with number"""

    name = "out-" + module

    if number is not None:
        name += number
    if ending is not None:
        name += ending

    return name

# Add later: provide a prefix for the name, timestamp, etc.
