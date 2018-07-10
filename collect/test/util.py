# -----------------------------------------------------------------------------
# util.py - Test utilities
#
# July 2018, Matt Ware
#
# -----------------------------------------------------------------------------

"""Test utilities."""


import os
import shutil
import unittest


__all__ = (
    "BaseTest",
)


class BaseTest(unittest.TestCase):
    _TEST_DIR = "/tmp/marple-test/"

    def setUp(self):
        """Per-test set-up"""
        os.makedirs(self._TEST_DIR, exist_ok=True)

    def tearDown(self):
        """Per-test tear-down"""
        shutil.rmtree(self._TEST_DIR)
