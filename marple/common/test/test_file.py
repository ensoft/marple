import unittest
from unittest import mock
from io import StringIO

from marple.common import (
    file,
    paths
)


class _FileBaseTest(unittest.TestCase):
    date, now = None, None

    # Override run to apply patches for all tests
    def run(self, result=None):
        with mock.patch('marple.common.file.datetime') as datetime:
            self.date = datetime
            self.now = self.date.now.return_value
            self.now.strftime.return_value = "date"
            super().run(result)


class TestDisplayFileName(_FileBaseTest):

    def test_empty(self):
        with self.assertRaises(FileNotFoundError) as fnfe:
            file.DisplayFileName(given_name="")
            err = fnfe.msg
            self.assertEqual("Cannot have empty file name.", err)

    def test_simple(self):
        dfn = file.DisplayFileName()
        self.assertEqual(paths.OUT_DIR + "date.marple.display", str(dfn))

    def test_custom_option(self):
        dfn = file.DisplayFileName("option")
        self.assertEqual(paths.OUT_DIR + "date_option.marple.display", str(dfn))

    def test_custom_extension(self):
        dfn = file.DisplayFileName(extension="extension")
        self.assertEqual(paths.OUT_DIR + "date.extension", str(dfn))

    def test_modification(self):
        dfn = file.DisplayFileName()
        dfn.set_options("option", "extension")
        self.assertEqual(paths.OUT_DIR + "date_option.extension", str(dfn))

    def test_custom_name(self):
        dfn = file.DisplayFileName(given_name="test")
        self.assertEqual(paths.OUT_DIR + "test", str(dfn))

    def test_custom_path(self):
        name = "/home/test"
        dfn = file.DisplayFileName(given_name=name)
        self.assertEqual(name, str(dfn))


class TestDataFileName(_FileBaseTest):
    def test_empty(self):
        with self.assertRaises(FileNotFoundError) as fnfe:
            file.DataFileName(given_name="")
            err = fnfe.msg
            self.assertEqual("Cannot have empty file name.", err)

    def test_simple(self):
        dfn = file.DataFileName()
        self.assertEqual(paths.OUT_DIR + "date.marple", str(dfn))

    def test_custom_name(self):
        dfn = file.DataFileName(given_name="test")
        self.assertEqual(paths.OUT_DIR + "test", str(dfn))

    def test_custom_path(self):
        name = "/home/test"
        dfn = file.DataFileName(given_name=name)
        self.assertEqual(name, str(dfn))

    @mock.patch('builtins.open')
    def test_export(self, open_mock):
        # Create mocks
        file_mock = StringIO()
        context_mock = open_mock.return_value
        context_mock.__enter__.return_value = file_mock

        dfn = file.DataFileName()
        dfn.export_filename()

        open_mock.assert_called_once_with(paths.VAR_DIR + "filename", "w")
        actual = file_mock.getvalue()
        expected = str(dfn)

        self.assertEqual(expected, actual)

    @mock.patch('marple.common.file.logger')
    @mock.patch('builtins.open')
    def test_import_fail(self, open_mock, log_mock):
        # Create mocks
        open_mock.side_effect = FileNotFoundError

        with self.assertRaises(FileNotFoundError):
            file.DataFileName.import_filename()

        open_mock.assert_called_once_with(paths.VAR_DIR + "filename", "r")
        log_mock.error.assert_called_once_with(
            'Unable to find filename helper file in %s', '/var/lib/')

    @mock.patch('builtins.open')
    def test_import_success(self, open_mock):
        # Create mocks
        file_mock = StringIO('test')
        context_mock = open_mock.return_value
        context_mock.__enter__.return_value = file_mock

        result = file.DataFileName.import_filename()
        self.assertEqual('test', result)
        open_mock.assert_called_once_with(paths.VAR_DIR + "filename", "r")


class TestTempFileName(_FileBaseTest):

    def test_simple(self):
        tfn = file.TempFileName()
        self.assertEqual(paths.TMP_DIR + "date.tmp", str(tfn))
