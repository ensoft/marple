import unittest
from unittest import mock

from marple.common import consts
from marple.display import main


class DisplayTest(unittest.TestCase):
    """
    Tests the display function from the controller

    """

    class MockDisplay:
        """
        Mock for all the display classes, that consumes the data from the
        sections

        """

        def __init__(self, data, *args):
            self.data = data

        def show(self):
            for _ in self.data.datum_generator:
                continue

    # TODO rewrite these tests to reflect new display main.py
    # Tests should NOT use a demo input file - that would be testing the data
    # reader too


class ArgsParseTest(unittest.TestCase):
    """
    Tests the args parse function from the controller

    """
    def test_args_normal(self):
        args = ['-fg', '-i', 'test.in']
        args = main._args_parse(args)
        self.assertTrue(args.flamegraph)
        self.assertEqual(args.infile, 'test.in')


class SelectModeTest(unittest.TestCase):
    """
    Tests the _select_mode function from the controller
    Will have a test for each possibility

    """
    # The following tests verify that, under normal condition, select works
    # for both args and config file

    def test_hm_args(self):
        mode = main._select_mode("Disk Latency/Time", "point",
                                 vars(main._args_parse(['-hm'])))
        self.assertEqual(mode, consts.DisplayOptions.HEATMAP)

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="heatmap")
    def test_hm_config(self, mock_opt):
        mode = main._select_mode("Disk Latency/Time", "point",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.HEATMAP)

    def test_tm_args(self):
        mode = main._select_mode("Malloc Stacks", "stack",
                                 vars(main._args_parse(['-tm'])))
        self.assertEqual(mode, consts.DisplayOptions.TREEMAP)

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="treemap")
    def test_tm_config(self, mock_opt):
        mode = main._select_mode("Malloc Stacks", "stack",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.TREEMAP)

    def test_fg_args(self):
        mode = main._select_mode("Call Stacks", "stack",
                                 vars(main._args_parse(['-fg'])))
        self.assertEqual(mode, consts.DisplayOptions.FLAMEGRAPH)

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="flamegraph")
    def test_fg_config(self, mock_opt):
        mode = main._select_mode("Call Stacks", "stack",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.FLAMEGRAPH)

    def test_sp_args(self):
        mode = main._select_mode("Memory/Time", "point",
                                 vars(main._args_parse(['-sp'])))
        self.assertEqual(mode, consts.DisplayOptions.STACKPLOT)

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="stackplot")
    def test_sp_config(self, mock_opt):
        mode = main._select_mode("Memory/Time", "point",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.STACKPLOT)

    def test_g2_args(self):
        mode = main._select_mode("Scheduling Events", "event",
                                 vars(
                                           main._args_parse(['-g2'])))
        self.assertEqual(mode, consts.DisplayOptions.G2)

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="g2")
    def test_g2_config(self, mock_opt):
        mode = main._select_mode("Scheduling Events", "event",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.G2)

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="g2")
    def test_invalid_arg_but_valid_config(self, mock_opt):
        """
        We call the select with an invalid arg for the datatype, but it will
        not trigger errors since we default it to the value from the config
        Covers all such test cases
        """

        mode = main._select_mode("Scheduling Events", "event",
                                 vars(main._args_parse(["-fg"])))
        self.assertEqual(mode, consts.DisplayOptions.G2)

    def test_invalid_interface_but_correct_mode(self):
        """
        Even though we have an invalid interface, since we have a cmd line
        argument that is consistent with the datatype, the answer is correct
        """

        mode = main._select_mode("INVALID", "event",
                                 vars(main._args_parse(["-g2"])))
        self.assertEqual(mode, consts.DisplayOptions.G2)

    # The following tests verify that errors are triggered correctly

    def test_datatype_not_supported(self):
        with self.assertRaises(ValueError) as ve:
            main._select_mode("RANDOM", "RANDOM",
                              vars(main._args_parse([])))
        err = ve.exception
        self.assertEqual(str(err),
                         "The datatype RANDOM is not supported.")

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="random")
    def test_invalid_default(self, mock_opt):
        """
        If the default value from the config is invalid, throw error

        """
        with self.assertRaises(ValueError) as ve:
            main._select_mode("Scheduling Events", "event",
                              vars(main._args_parse([])))
        err = ve.exception
        self.assertEqual(
            "The default value from the config (random) was not recognised. "
            "Make sure the config values are within the accepted parameters.",
            str(err))

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="heatmap")
    def test_invalid_match(self, mock_opt):
        """
        If the default value from the config is valid but not supported by the
        file

        """
        with self.assertRaises(ValueError) as ve:
            main._select_mode("Scheduling Events", "event",
                              vars(main._args_parse([])))
        err = ve.exception
        self.assertEqual(str(err),
                         "No valid args or config values found for "
                         "Scheduling Events. Either add an arg in the terminal "
                         "command or modify the config file")

    @mock.patch("marple.common.config.get_option_from_section",
                return_value="heatmap")
    def test_invalid_(self, mock_opt):
        """
        If the default value from the config is valid but not supported by the
        file

        """
        with self.assertRaises(ValueError) as ve:
            main._select_mode("Scheduling Events", "event",
                              vars(main._args_parse([])))
        err = ve.exception
        self.assertEqual(str(err),
                         "No valid args or config values found for "
                         "Scheduling Events. Either add an arg in the terminal "
                         "command or modify the config file")