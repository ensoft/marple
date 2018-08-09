# -------------------------------------------------------------
# paths.py - stores standard paths to files
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""Stores standard paths to files"""
__all__ = ["create_directories"]

import os
import main

LOG_DIR = "/var/log/marple/"
TMP_DIR = "/tmp/marple/"
VAR_DIR = "/var/lib/"

MARPLE_DIR = os.path.dirname(os.path.abspath(main.__file__))
OUT_DIR = os.getcwd() + "/marple_out/"

def create_directories():
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)
    if not os.path.isdir(TMP_DIR):
        os.mkdir(TMP_DIR)
    if not os.path.isdir(VAR_DIR):
        os.mkdir(VAR_DIR)
    if not os.path.isdir(OUT_DIR):
        os.mkdir(OUT_DIR)
