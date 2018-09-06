import unittest
from io import StringIO
from unittest import mock

from marple.common import consts, data_io
from marple.display import (
    main
)
from marple.display.interface import heatmap, treemap, g2, flamegraph, stackplot


class DisplayTest(unittest.TestCase):
    """
    Tests the display function from the controller

    """
    file = \
        "{\"start\": \"2018-08-20 18:46:38.403129\", \"end\":" \
        " \"2018-08-20 18:46:39.403129\", \"datatype\": \"point\"," \
        "\"interface\": \"memtime\"}\n" \
        "Dummy Line\n" \
        "\n" \
        "{\"start\": \"2018-08-20 18:46:38.403129\", \"end\": " \
        "\"2018-08-20 18:46:39.403129\", \"datatype\": \"event\"" \
        ", \"interface\": \"cpusched\"}\n" \
        "Dummy Line\n" \
        "\n" \
        "{\"start\": \"2018-08-20 18:46:38.403129\", \"end\": " \
        "\"2018-08-20 18:46:39.403129\", \"datatype\": \"stack\"" \
        ", \"interface\": \"memleak\"}\n" \
        "Dummy Line\n" \
        "\n" \
        "{\"start\": \"2018-08-20 18:46:38.403129\", \"end\": " \
        "\"2018-08-20 18:46:39.403129\", \"datatype\": \"point\"" \
        ", \"interface\": \"disklat\"}\n" \
        "Dummy Line\n" \
        "\n" \
        "{\"start\": \"2018-08-20 18:46:38.403129\", \"end\": " \
        "\"2018-08-20 18:46:39.403129\", \"datatype\": \"stack\"" \
        ", \"interface\": \"mallocstacks\"}\n" \
        "Dummy Line\n" \
        "\n"

    class MockDisplay:
        """
        Mock for all the display classes, that consumes the data from the
        sections

        """

        def __init__(self, data, *args):
            self.data = data

        def show(self):
            for _ in self.data:
                continue

    @mock.patch("marple.display.interface.stackplot.StackPlot")
    @mock.patch("marple.display.interface.treemap.Treemap")
    @mock.patch("marple.display.interface.flamegraph.Flamegraph")
    @mock.patch("marple.display.interface.g2.G2")
    @mock.patch("marple.display.interface.heatmap.HeatMap")
    @mock.patch("marple.display.main.open")
    @mock.patch("marple.display.main._get_display_options")
    @mock.patch("marple.display.main._get_data_options")
    def test_display_no_args_only_config(self, data_options_mock,
                                         display_options_mock, open_mock,
                                         hm, g2, fg, tm, sp):
        """
        Testing using a file that contains all the datatypes; we only use the
        config

        """
        open_mock.side_effect = [StringIO(self.file)]
        hm.side_effect = self.MockDisplay
        g2.side_effect = self.MockDisplay
        fg.side_effect = self.MockDisplay
        tm.side_effect = self.MockDisplay
        sp.side_effect = self.MockDisplay

        args = ['-i', 'test.in', '-o', 'test.out']
        args = main._args_parse(args)

        main._display(args)
        # Check if each one of them is called
        self.assertTrue(fg.call_count == 1 and
                        sp.call_count == 1 and
                        hm.call_count == 1 and
                        tm.call_count == 1 and
                        g2.call_count == 1)

    @mock.patch("marple.display.interface.stackplot.StackPlot")
    @mock.patch("marple.display.interface.treemap.Treemap")
    @mock.patch("marple.display.interface.flamegraph.Flamegraph")
    @mock.patch("marple.display.interface.g2.G2")
    @mock.patch("marple.display.interface.heatmap.HeatMap")
    @mock.patch("marple.display.main.open")
    @mock.patch("marple.display.main._get_display_options")
    @mock.patch("marple.display.main._get_data_options")
    def test_display_args(self, data_options_mock,
                          display_options_mock, open_mock,
                          hm, g2, fg, tm, sp):
        """
        Testing using a file that contains all the datatypes; we only use the
        config

        """
        # File objects for each of the argument sets
        open_mock.side_effect = [StringIO(self.file),
                                 StringIO(self.file),
                                 StringIO(self.file)]
        hm.side_effect = self.MockDisplay
        g2.side_effect = self.MockDisplay
        fg.side_effect = self.MockDisplay
        tm.side_effect = self.MockDisplay
        sp.side_effect = self.MockDisplay

        # First set of args
        args = ['-sp', '-g2', '-tm', '-i', 'test.in', '-o', 'test.out']
        args = main._args_parse(args)
        main._display(args)
        # Check if each one of them is called
        self.assertTrue(fg.call_count == 0 and
                        sp.call_count == 2 and
                        hm.call_count == 0 and
                        tm.call_count == 2 and
                        g2.call_count == 1)

        # Second set of args
        g2.reset_mock()
        fg.reset_mock()
        tm.reset_mock()
        sp.reset_mock()
        hm.reset_mock()

        args = ['-fg', '-g2', '-hm', '-i', 'test.in', '-o', 'test.out']
        args = main._args_parse(args)
        main._display(args)
        # Check if each one of them is called
        self.assertTrue(fg.call_count == 2 and
                        sp.call_count == 0 and
                        hm.call_count == 2 and
                        tm.call_count == 0 and
                        g2.call_count == 1)

        # Third set of args
        g2.reset_mock()
        fg.reset_mock()
        tm.reset_mock()
        sp.reset_mock()
        hm.reset_mock()

        args = ['-sp', '-i', 'test.in', '-o', 'test.out']
        args = main._args_parse(args)
        main._display(args)
        # Check if each one of them is called
        self.assertTrue(fg.call_count == 1 and
                        sp.call_count == 2 and
                        hm.call_count == 0 and
                        tm.call_count == 1 and
                        g2.call_count == 1)


class ArgsParseTest(unittest.TestCase):
    """
    Tests the args parse function from the controller

    """
    def test_args_normal(self):
        args = ['-fg', '-i', 'test.in', '-o', 'test.out']
        args = main._args_parse(args)
        self.assertTrue(args.flamegraph)
        self.assertEqual(args.infile, 'test.in')
        self.assertEqual(args.outfile, 'test.out')


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

    @mock.patch("marple.common.config.Parser.get_option_from_section",
                return_value="heatmap")
    def test_hm_config(self, mock_opt):
        mode = main._select_mode("Disk Latency/Time", "point",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.HEATMAP)

    def test_tm_args(self):
        mode = main._select_mode("Malloc Stacks", "stack",
                                 vars(main._args_parse(['-tm'])))
        self.assertEqual(mode, consts.DisplayOptions.TREEMAP)

    @mock.patch("marple.common.config.Parser.get_option_from_section",
                return_value="treemap")
    def test_tm_config(self, mock_opt):
        mode = main._select_mode("Malloc Stacks", "stack",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.TREEMAP)

    def test_fg_args(self):
        mode = main._select_mode("Call Stacks", "stack",
                                 vars(main._args_parse(['-fg'])))
        self.assertEqual(mode, consts.DisplayOptions.FLAMEGRAPH)

    @mock.patch("marple.common.config.Parser.get_option_from_section",
                return_value="flamegraph")
    def test_fg_config(self, mock_opt):
        mode = main._select_mode("Call Stacks", "stack",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.FLAMEGRAPH)

    def test_sp_args(self):
        mode = main._select_mode("Memory/Time", "point",
                                 vars(main._args_parse(['-sp'])))
        self.assertEqual(mode, consts.DisplayOptions.STACKPLOT)

    @mock.patch("marple.common.config.Parser.get_option_from_section",
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

    @mock.patch("marple.common.config.Parser.get_option_from_section",
                return_value="g2")
    def test_g2_config(self, mock_opt):
        mode = main._select_mode("Scheduling Events", "event",
                                 vars(main._args_parse([])))
        self.assertEqual(mode, consts.DisplayOptions.G2)

    @mock.patch("marple.common.config.Parser.get_option_from_section",
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
                         "The datatype RANDOM is not supported")

    @mock.patch("marple.common.config.Parser.get_option_from_section",
                return_value="random")
    def test_invalid_default(self, mock_opt):
        """
        If the default value from the config is invalid, throw error

        """
        with self.assertRaises(ValueError) as ve:
            main._select_mode("Scheduling Events", "event",
                              vars(main._args_parse([])))
        err = ve.exception
        self.assertEqual(str(err),
                         "The default value from the config could not be "
                         "converted to a consts.DisplayOptions enum. Check "
                         "that the values in the config correspond with the "
                         "enum values.")

    @mock.patch("marple.common.config.Parser.get_option_from_section",
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

    @mock.patch("marple.common.config.Parser.get_option_from_section",
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


class TestDataOptions(unittest.TestCase):
    """
    Tests the _get_data_options function from the controller
    Will have a test for each possibility

    """
    def test_stack(self):
        """
        Testing the stack datatype

        """
        header = {"datatype": "stack", "data_options": {"weight_units": "kb"}}
        opts = main._get_data_options(header)
        self.assertEqual(opts, data_io.StackData.DataOptions("kb"))

    def test_point(self):
        """
        Testing the point datatype

        """
        header = {"datatype": "point", "data_options":
                     {
                         "x_label": "xlabel",
                         "x_units": "xunits",
                         "y_label": "ylabel",
                         "y_units": "yunits"
                     }
                 }
        opts = main._get_data_options(header)
        self.assertEqual(opts, data_io.PointData.DataOptions(
            "xlabel", "ylabel", "xunits", "yunits"))

    def test_event(self):
        """
        Testing the event datatype

        """
        header = {"datatype": "event", "data_options": {}}
        opts = main._get_data_options(header)
        self.assertEqual(opts, None)

    def test_invalid_datatype(self):
        """
        Testing the event datatype

        """
        header = {"datatype": "RANDOM", "data_options": {}}
        with self.assertRaises(ValueError):
            main._get_data_options(header)


class TestDisplayOptions(unittest.TestCase):
    """
    Class that tests if the Display options correctly retrieved

    """
    @mock.patch("marple.common.config.Parser.get_option_from_section")
    def test_flamegraph(self, mock_opt):
        """
        Display options for flamegraph retrieved correctly

        """
        mock_opt.side_effect = ['hot']

        opt = main._get_display_options(consts.DisplayOptions.FLAMEGRAPH)
        self.assertEqual(opt,
                         flamegraph.Flamegraph.DisplayOptions(coloring='hot'))

    @mock.patch("marple.common.config.Parser.get_option_from_section")
    def test_heatmap(self, mock_opt):
        """
        Display options for heatmap retrieved correctly

        """
        mock_opt.side_effect = [1.0, 1.0, 1.0, True]

        opt = main._get_display_options(consts.DisplayOptions.HEATMAP)
        self.assertEqual(opt, heatmap.HeatMap.DisplayOptions(
                                  'No. Occurences',
                                  heatmap.GraphParameters(figure_size=1,
                                                          y_res=1,
                                                          scale=1), True))

    @mock.patch("marple.common.config.Parser.get_option_from_section")
    def test_g2(self, mock_opt):
        """
        Display options for g2 retrieved correctly

        """
        mock_opt.side_effect = ["pid"]

        opt = main._get_display_options(consts.DisplayOptions.G2)
        self.assertEqual(opt, g2.G2.DisplayOptions("pid"))

    @mock.patch("marple.common.config.Parser.get_option_from_section")
    def test_treemap(self, mock_opt):
        """
        Display options for treemap retrieved correctly

        """
        mock_opt.side_effect = [25]

        opt = main._get_display_options(consts.DisplayOptions.TREEMAP)
        self.assertEqual(opt, treemap.Treemap.DisplayOptions(25))

    @mock.patch("marple.common.config.Parser.get_option_from_section")
    def test_stackplot(self, mock_opt):
        """
        Display options for stackplot retrieved correctly

        """
        mock_opt.side_effect = [25]

        opt = main._get_display_options(consts.DisplayOptions.STACKPLOT)
        self.assertEqual(opt, stackplot.StackPlot.DisplayOptions(25))