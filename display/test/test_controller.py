import display.test.util_display as util
import json

from unittest.mock import patch, ANY
from common import file
from unittest import mock
from display import controller


class _BaseTest(util.BaseTest):
    """Base test class"""


class DisplayTest(_BaseTest):
    """
    Tests the display function from the controller

    """
    class MockedReader:
        """
        Class used to mock the context manager Reader
        """
        def __init__(self, file):
            pass

        def __enter__(self):
            js = "{\"start\": \"2018-08-20 18:46:38.403129\", \"end\": " \
                 "\"2018-08-20 18:46:39.403129\", \"datatype\": \"Event" \
                 " Data\", \"interface\": \"Memory/Time\"}"
            return json.loads(js), ""

        def __exit__(self, *args):
            pass

    @mock.patch("display.stackplot.StackPlot.__init__", return_value=None)
    @mock.patch("display.controller._select_mode",
                return_value=controller.DisplayOptions.STACKPLOT)
    @mock.patch("display.stackplot.StackPlot.show")
    def test_display(self, show_mock, select_mock, sp_mock):
        """
        Testing if the display reaches the show method safely in a normal case
        It covers every file type since we simply hard code it

        """
        with mock.patch("collect.IO.read.Reader", self.MockedReader):
            args = ['-sp', '-i', 'test.in', '-o', 'test.out']
            args = controller._args_parse(args)
            controller._display(args)

        show_mock.assert_called_once()
        sp_mock.assert_called_once()

    @mock.patch("display.controller._select_mode", return_value="foobar")
    def test_display_filetype_unrecognized(self, select_mock):
        """
        Testing if the display method throws an error if the filetype is
        unrecognized

        """
        with self.assertRaises(ValueError), \
             mock.patch("collect.IO.read.Reader", self.MockedReader):
            args = ['-sp', '-i', 'test.in', '-o', 'test.out']
            args = controller._args_parse(args)
            controller._display(args)


class ArgsParseTest(_BaseTest):
    """
    Tests the args parse function from the controller

    """
    def test_args_normal(self):
        args = ['-fg', '-i', 'test.in', '-o', 'test.out']
        args = controller._args_parse(args)
        self.assertTrue(args.flamegraph)
        self.assertEqual(args.infile, 'test.in')
        self.assertEqual(args.outfile, 'test.out')


class SelectModeTest(_BaseTest):
    """
    Tests the _select_mode function from the controller
    Will have a test for each possibility

    """
    # The following tests verify that, under normal condition, select works
    # for both args and config file

    def test_hm_args(self):
        mode = controller._select_mode("Disk Latency/Time",
                                       vars(controller._args_parse(['-hm'])))
        self.assertEqual(mode, controller.DisplayOptions.HEATMAP)

    @mock.patch("common.config.Parser.get_option_from_section",
                return_value="heatmap")
    def test_hm_config(self, mock_opt):
        mode = controller._select_mode("Disk Latency/Time",
                                       vars(controller._args_parse([])))
        self.assertEqual(mode, controller.DisplayOptions.HEATMAP)

    def test_tm_args(self):
        mode = controller._select_mode("Malloc Stacks",
                                       vars(controller._args_parse(['-tm'])))
        self.assertEqual(mode, controller.DisplayOptions.TREEMAP)

    @mock.patch("common.config.Parser.get_option_from_section",
                return_value="treemap")
    def test_tm_config(self, mock_opt):
        mode = controller._select_mode("Malloc Stacks",
                                       vars(controller._args_parse([])))
        self.assertEqual(mode, controller.DisplayOptions.TREEMAP)

    def test_fg_args(self):
        mode = controller._select_mode("Call Stacks",
                                       vars(controller._args_parse(['-fg'])))
        self.assertEqual(mode, controller.DisplayOptions.FLAMEGRAPH)

    @mock.patch("common.config.Parser.get_option_from_section",
                return_value="flamegraph")
    def test_fg_config(self, mock_opt):
        mode = controller._select_mode("Call Stacks",
                                       vars(controller._args_parse([])))
        self.assertEqual(mode, controller.DisplayOptions.FLAMEGRAPH)

    def test_sp_args(self):
        mode = controller._select_mode("Memory/Time",
                                       vars(controller._args_parse(['-sp'])))
        self.assertEqual(mode, controller.DisplayOptions.STACKPLOT)

    @mock.patch("common.config.Parser.get_option_from_section",
                return_value="stackplot")
    def test_sp_config(self, mock_opt):
        mode = controller._select_mode("Memory/Time",
                                       vars(controller._args_parse([])))
        self.assertEqual(mode, controller.DisplayOptions.STACKPLOT)

    def test_g2_args(self):
        mode = controller._select_mode("Scheduling Events",
                                       vars(
                                           controller._args_parse(['-g2'])))
        self.assertEqual(mode, controller.DisplayOptions.G2)

    @mock.patch("common.config.Parser.get_option_from_section",
                return_value="g2")
    def test_g2_config(self, mock_opt):
        mode = controller._select_mode("Scheduling Events",
                                       vars(controller._args_parse([])))
        self.assertEqual(mode, controller.DisplayOptions.G2)

    @mock.patch("common.config.Parser.get_option_from_section",
                return_value="g2")
    def test_invalid_arg_but_valid_config(self, mock_opt):
        """
        We call the select with an invalid arg
        Covers all other cases (if it doesn't use the args it will used the
        config, which we tested the config above)
        """

        mode = controller._select_mode("Scheduling Events",
                                       vars(controller._args_parse(["-fg"])))
        self.assertEqual(mode, controller.DisplayOptions.G2)

    # The following tests verify that errors are triggered correctly

    def test_file_not_supported(self):
        with self.assertRaises(ValueError) as ve:
            controller._select_mode("RANDOM",
                                    vars(controller._args_parse([])))
        err = ve.exception
        self.assertEqual(str(err),
                         "The file type RANDOM is not supported")

    @mock.patch("common.config.Parser.get_option_from_section",
                return_value="random")
    def test_invalid_default(self, mock_opt):
        """
        If the default value from the config is invalid, throw error

        """
        with self.assertRaises(ValueError) as ve:
            controller._select_mode("Scheduling Events",
                                    vars(controller._args_parse([])))
        err = ve.exception
        self.assertEqual(str(err),
                         "The default value from the config could not be "
                         "converted to a DisplayOptions enum. Check that the "
                         "values in the config correspond with the "
                         "enum values.")

    @mock.patch("common.config.Parser.get_option_from_section",
                return_value="heatmap")
    def test_invalid_match(self, mock_opt):
        """
        If the default value from the config is valid but not supported by the
        file

        """
        with self.assertRaises(ValueError) as ve:
            controller._select_mode("Scheduling Events",
                                    vars(controller._args_parse([])))
        err = ve.exception
        self.assertEqual(str(err),
                         "No valid args or config values found for "
                         "Scheduling Events. Either add an arg in the terminal "
                         "command or modify the config file")
