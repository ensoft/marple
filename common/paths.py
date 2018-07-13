# -------------------------------------------------------------
# paths.py - stores standard paths to files
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""Stores standard paths to files"""
import os

OUT_DIR = "out/"
TMP_DIR = "/tmp/marple/"
VAR_DIR = "/var/lib/"


def mkdirs():
    """Creates directories for output files"""
    if not os.path.isdir(OUT_DIR):
        os.mkdir(OUT_DIR)
