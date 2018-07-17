from unittest.mock import patch

import collect.test.util as util

import os.path as path
import common.config as config
import common.file as file
import collect.controller.cpu as sched
import collect.controller.main as collect_parser

# -----------------------------------------------------------------------------
# Helpers
#


class _BaseTest(util.BaseTest):
    """Base test class for controller testing."""


# -----------------------------------------------------------------------------
# Tests
#

class _ParseTest(_BaseTest):
    """Class for testing that parsing works correctly"""
    @staticmethod
    def check_calls(argv, cls, fn, args):
        """
        Stubs out a given function and checks that it gets called
        after correctly passing the input.

        :param argv:
            The arguments passed to the main function.
        :param cls:
            The class or module from which to take the function.
        :param fn:
            The function that should be stubbed out and get called.
        :param args:
            The arguments to the function that was stubbed out.
        """
        with patch.object(cls, fn) as call_mock:
            collect_parser.main(argv)
            call_mock.assert_called_once_with(args)


class SchedTest(_ParseTest):
    def test_sched_collect(self):
        """Check that asking for sched calls the right function"""
        self.check_calls(["--sched", "-t", "13"], sched, "collect", 13)

    @patch.object(sched, 'collect')
    def test_sched_collect_config_time(self, collect_sched):
        """Check that config default time is used if set in config"""
        with patch.object(config, "get_default_time", return_value=7) \
                as get_time_mock:
            collect_parser.main(["--sched"])
            get_time_mock.assert_called_once()
            collect_sched.assert_called_once_with(7)

    @patch.object(sched, 'collect')
    def test_sched_collect_default_time(self, collect_sched):
        """Check that module default time is used if not set in config"""
        with patch.object(config, "get_default_time", return_value=None) \
                as get_time_mock:
            collect_parser.main(["--sched"])
            get_time_mock.assert_called_once()
            collect_sched.assert_called_once_with(10)

    @patch.object(sched, 'collect')
    def test_sched_collect_create_filename(self, collect_sched):
        """Check that file default function is called to create filename"""
        with patch.object(file, "create_unique_temp_name") \
                as get_filename_mock:
            collect_parser.main(["--sched"])
            get_filename_mock.assert_called_once()
            self.assertTrue(collect_sched.called)

    @patch.object(sched, 'collect')
    def test_sched_collect_auto_filename_exists(self, collect_sched):
        """Check that it retries 5 times if auto create filename fails"""
        with patch.object(file, "create_unique_temp_name") \
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

    @patch.object(sched, 'collect')
    def test_sched_collect_user_filename_exists(self, collect_sched):
        """Check that the program exits if user puts existing filename"""
        with patch.object(path, "isfile", return_value=True):
            with self.assertRaises(SystemExit):
                collect_parser.main(["--sched", "-f", "test_name"])
            self.assertFalse(collect_sched.called)
