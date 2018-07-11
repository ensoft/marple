# -------------------------------------------------------------
# file.py - generates unique file names
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Generates unique file names

Provides functions to generate a filename if no name was provided by the user.

"""

__all__ = ["create_name"]

import uuid


def create_name():
    """Create a new unique generic name for a file"""
    # TODO: only create filename, add tmp as needed when creating the file
    return "tmp/" + str(uuid.uuid4()) + ".tmp"

# Add later: provide a prefix for the name, timestamp, etc.
