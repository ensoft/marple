from unittest.mock import patch

import collect.test.util as util

import os.path as path
import common.config as config
import common.file as file
import collect.controller.sched as sched
import collect.controller.main as collect_parser

# -----------------------------------------------------------------------------
# Helpers
#


class _BaseTest(util.BaseTest):
    """Base test class for perf testing."""
    pass


class _ParseTest(_BaseTest):
    """Class for testing that parsing works correctly"""


class SchedTest(_BaseTest):

    @patch.object(sched, 'collect_all')
    def test_sched_collect_config_time(self, collect_sched):
        with patch.object(config, "get_default_time", return_value=7) \
                as get_time_mock:
            collect_parser.main(["--sched"])
            get_time_mock.assert_called_once()
            collect_sched.assert_called_once_with(7)

    @patch.object(sched, 'collect_all')
    def test_sched_collect_default_time(self, collect_sched):
        with patch.object(config, "get_default_time", return_value=None) \
                as get_time_mock:
            collect_parser.main(["--sched"])
            get_time_mock.assert_called_once()
            collect_sched.assert_called_once_with(10)

    @patch.object(sched, 'collect_all')
    def test_sched_collect_create_filename(self, collect_sched):
        with patch.object(file, "create_name") \
                as get_filename_mock:
            collect_parser.main(["--sched"])
            get_filename_mock.assert_called_once()
            self.assertTrue(collect_sched.called)

    @patch.object(sched, 'collect_all')
    def test_sched_collect_auto_filename_exists(self, collect_sched):
        with patch.object(file, "create_name") \
                as get_filename_mock, \
                patch.object(path, "isfile", return_value=True) \
                as is_file_mock:
            with self.assertRaises(SystemExit):
                collect_parser.main(["--sched"])
            self.assertTrue(is_file_mock.called)
            self.assertTrue(is_file_mock.call_count == 7)
            self.assertTrue(get_filename_mock.called)
            self.assertTrue(get_filename_mock.call_count == 6)
            self.assertFalse(collect_sched.called)

    @patch.object(sched, 'collect_all')
    def test_sched_collect_user_filename_exists(self, collect_sched):
        with patch.object(path, "isfile", return_value=True):
            with self.assertRaises(SystemExit):
                collect_parser.main(["--sched", "-f", "test_name"])
            self.assertFalse(collect_sched.called)
