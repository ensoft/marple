from unittest.mock import patch

import collect.controller.cpu as cpu
import collect.controller.main as collect_parser
import collect.test.util as util
import common.config as config


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
    def check_calls(argv, cls, fn, args, kwargs={}):
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
        :param kwargs:
            The keyword arguments to the function that was stubbed out.
        """
        with patch.object(cls, fn) as call_mock:
            collect_parser.main(argv)
            call_mock.assert_called_once_with(*args, **kwargs)


@patch("common.file.export_out_filename")
@patch("common.file.create_out_filename_generic")
class SchedTest(_ParseTest):
    def test_controller_logic(self, filename_generator, export):
        """Check that asking for cpu calls the right function"""
        filename_generator.return_value = "filename"
        self.check_calls(["--cpu", "-t", "13"], cpu,
                         "sched_collect_and_store", args=(13, "filename"))

    @patch.object(cpu, "sched_collect_and_store")
    def test_sched_collect_config_time(self, collect_sched,
                                       filename_generator, export):
        """Check that config default time is used if set in config"""
        filename_generator.return_value = "filename"
        with patch.object(config, "get_default_time", return_value=7) \
                as get_time_mock:
            collect_parser.main(["--cpu"])
            get_time_mock.assert_called()
            collect_sched.assert_called_once_with(7, "filename")

    @patch.object(cpu, "sched_collect_and_store")
    def test_sched_collect_default_time(self, collect_sched,
                                        filename_generator, export):
        """Check that module default time is used if not set in config"""
        filename_generator.return_value = "filename"
        with patch.object(config, "get_default_time", return_value=None) \
                as get_time_mock:
            collect_parser.main(["--cpu"])
            get_time_mock.assert_called_once()
            collect_sched.assert_called_once_with(10, "filename")

    @patch.object(cpu, "sched_collect_and_store")
    def test_sched_collect_create_filename(self, collect_sched,
                                           filename_generator, export):
        """Check that file default function is called to create filename"""
        collect_parser.main(["--cpu"])
        filename_generator.assert_called_once()
        self.assertTrue(collect_sched.called)
