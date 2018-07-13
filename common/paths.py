# -------------------------------------------------------------
# paths.py - stores standard paths to files
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""Stores standard paths to files"""
__all__ = ["create_directories"]

import os

LOG_DIR = "/var/log/marple/"
TMP_DIR = "/tmp/marple/"
VAR_DIR = "/var/lib/"


def create_directories():
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)
    if not os.path.isdir(TMP_DIR):
        os.mkdir(TMP_DIR)
    if not os.path.isdir(VAR_DIR):
        os.mkdir(VAR_DIR)
