# -------------------------------------------------------------
# plotter.py - plots event data
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

"""
Tests the event plotter

"""

import unittest
from unittest import mock

from marple.common import data_io
from marple.display.interface import plotter


class _BasePlotterTest(unittest.TestCase):
    """
    A base class that has some basic sets of events (used to build processed
    data in the various classes from the module

    """
    def setUp(self):
        self.standalone_events = [data_io.EventDatum(
            time=i,
            type="type1",
            specific_datum={
                "pid": 1,
                "comm": str(i),
                "cpu": 5
            },
            connected=None
        ) for i in range(1, 3)]

        self.connected_events = [data_io.EventDatum(
            time=i,
            type="type2",
            specific_datum={
                "source_pid": 2,
                "source_comm": str(i),
                "dest_pid": 3,
                "dest_comm": str(i + 10),
                "net_ns": 10
            },
            connected=[('source_', 'dest_')]
        ) for i in range(1, 3)]

        self.multiple_types = [data_io.EventDatum(
            time=1,
            type="type" + str(i),
            specific_datum={
                "source_pid": 1,
                "source_comm": '1',
                "dest_pid": 1,
                "dest_comm": '1',
                "net_ns": 1
            },
            connected=[('source_', 'dest_')]
        ) for i in range(9)]


class EventDataProcessorTest(_BasePlotterTest):
    """
    Tests the data processing class

    """
    def setUp(self):
        """
        We setup the processed data

        """
        super().setUp()
        # Object to test the functionality on (for testing we create another
        # one)
        self.edp = plotter._EventDataProcessor(self.standalone_events +
                                               self.connected_events)

    @mock.patch("marple.display.interface.plotter._EventDataProcessor._process_data")
    @mock.patch("marple.display.interface.plotter._EventDataProcessor._normalise")
    def test_init(self, normalise_mock, proc_dat_mock):
        """
        Test the init

        """
        proc_dat_mock.return_value = None, None, None

        plotter._EventDataProcessor(['ev1', 'ev2'])
        proc_dat_mock.assert_called_once_with(['ev1', 'ev2'])
        normalise_mock.assert_called_once()

    def test_data_processing(self):
        """
        We test the data processing step

        """
        part, prop, min_time = plotter._EventDataProcessor._process_data(
            self.standalone_events + self.connected_events)

        # Test the partitioning
        self.assertListEqual(part['type1'], self.standalone_events)
        self.assertListEqual(part['type2'], self.connected_events)

        self.assertSetEqual(prop,
                            {'comm', 'pid', 'cpu', 'net_ns'})

        self.assertEqual(min_time, 1)

    def test_normalised(self):
        """
        We test the if the times are normalised to 0

        """
        self.assertListEqual(sorted([event.time for event in
                                    self.edp.event_partition['type1']] +
                                    [event.time for event in
                                    self.edp.event_partition['type2']]),
                             sorted([0, 0, 1, 1]))

    def test_get_all_events(self):
        """
        Test if all the events are returned

        """
        self.assertListEqual(self.edp.get_all_events(),
                             self.edp.event_partition['type1'] +
                             self.edp.event_partition['type2'])

    def test_get_property_value(self):
        """
        Test if the property retrieval works (especially if it has problems
        with the prefixes (source_pid and dest_pid should be treated both as
        pid)

        """
        event_sa = self.standalone_events[0]
        event_conn = self.connected_events[0]

        # Test for a standalone (no prefix)
        self.assertEqual(plotter._EventDataProcessor.get_property_value(
            event_sa, 'pid'), '1')
        # Test if None is returned if the property does not exist
        self.assertEqual(plotter._EventDataProcessor.get_property_value(
            event_sa, 'not_prop'), None)

        # Test for a connected event (source and dest prefixes)
        self.assertEqual(plotter._EventDataProcessor.get_property_value(
            event_conn, 'pid', 'source_'), '2')
        self.assertEqual(plotter._EventDataProcessor.get_property_value(
            event_conn, 'pid', 'dest_'), '3')
        # Again, test if None is returned if the property does not exist,
        # now for connected events
        self.assertEqual(plotter._EventDataProcessor.get_property_value(
            event_conn, 'pid', 'sourc_'), None)


class PlotContainerBasicTest(_BasePlotterTest):
    """
    Tests the plot container class

    """
    def setUp(self):
        super().setUp()
        # Normal set of datum
        self.normal_data = plotter._EventDataProcessor(
            self.standalone_events + self.connected_events
        )
        # Set of datum that has multiple types and duplicate tracks
        self.edge_data = plotter._EventDataProcessor(
            self.multiple_types
        )
        self.y_axis_ticks = ['comm', 'pid']

    def _check_init(self, container, exp_ymap, exp_cmap, max_x, max_y):
        """
        Helper function that checks the state of the object after the init is
        what was expected

        """
        self.assertDictEqual(exp_ymap, container.tracks_ymap)
        self.assertDictEqual(exp_cmap, container.color_map)
        self.assertEqual(max_x, container.max_x)
        self.assertEqual(max_y, container.max_y)

    @mock.patch("marple.display.interface.plotter.pg")
    def test_init_normal(self, mock_pg):
        # tracks that would be created by the mapping function from events in
        # the list standalong + connected
        tracks = ["1,1", "2,1", "1,2", "11,3", "2,2", "12,3"]
        # Create the y map
        exp_ymap = dict([(tracks[idx], idx) for idx in range(6)])
        # Create the color map manually
        exp_color_map = {
            'type1': plotter._PlotContainer.line_colors[0],
            'type2': plotter._PlotContainer.line_colors[1],
        }        # Max x and y coordinates for the normal dataset
        exp_x = 1
        exp_y = 5
        init_container = plotter._PlotContainer(self.normal_data,
                                                self.y_axis_ticks)
        self._check_init(init_container, exp_ymap, exp_color_map, exp_x, exp_y)

    @mock.patch("marple.display.interface.plotter.pg")
    @mock.patch("marple.display.interface.plotter.colorsys")
    def test_init_edge(self, color_mock, mock_pg):
        """
        Tests the init function to see if the colors
        behave as expected (when we have more types than the number of hardcoded
        colors) or if we have the same tracks multiple times

        """
        color_mock.hls_to_rgb.return_value = (0, 0, 0)
        init_container = plotter._PlotContainer(self.edge_data,
                                                self.y_axis_ticks)
        exp_ymap = {'1,1': 0}
        exp_color_map = dict([('type' + str(i),
                              plotter._PlotContainer.line_colors[i]) for
                              i in range(7)] +
                             [('type7', (0, 0, 0)), ('type8', (0, 0, 0))])
        exp_x = 0
        exp_y = 0
        self._check_init(init_container, exp_ymap, exp_color_map, exp_x, exp_y)

    def test_concat(self):
        """
        Testing the function that transforms a list of lists into a list

        """
        exp = [1, 2, 3, 4, 5]
        inp = [[1], [2, 3], [4], [5]]
        self.assertEqual(exp, list(plotter._PlotContainer._concat(inp)))

    @mock.patch("marple.display.interface.plotter.pg")
    def test_empties(self, pg_mock):
        """
        Testing if the empty plot function behaves as expected

        """
        test_container = plotter._PlotContainer(self.normal_data,
                                                self.y_axis_ticks)
        test_container.empty_plot('highlight')
        pg_mock.PlotItem().plot().setData.assert_called_with([], [])

        test_container.empty_plot('type1')
        pg_mock.PlotItem().plot().setData.assert_called_with([], [],
                                                             symbol=[],
                                                             symbolBrush=[])

    @mock.patch("marple.display.interface.plotter.pg")
    def test_empty_all(self, pg_mock):
        """
        Testing if the empty all plots function calls the right number of times
        empty_plot (which calls setData, so we check that)

        """
        test_container = plotter._PlotContainer(self.normal_data,
                                                self.y_axis_ticks)
        test_container.empty_all_plots()

        # Called once for the helper, twice for the two event plots
        self.assertTrue(pg_mock.PlotItem().plot().setData.call_count == 3)

    @mock.patch("marple.display.interface.plotter.pg")
    def test_draw(self, pg_mock):
        """
        Test if the draw method creates the correct symbols, brushes and coord
        arrays before drawing (for both standalone and connected events)

        """
        test_container = plotter._PlotContainer(self.normal_data,
                                                self.y_axis_ticks)
        # First connected
        test_container.draw('type2')

        symbol = ['s', 'o', 's', 'o']
        symbol_brushes = [plotter._PlotContainer.source_brush,
                          plotter._PlotContainer.destination_brush,
                          plotter._PlotContainer.source_brush,
                          plotter._PlotContainer.destination_brush]
        pen = test_container.color_map['type2']
        pg_mock.PlotItem().plot().setData.assert_called_with(
            {'x': [0, 0, 1, 1], 'y': [2, 3, 4, 5]},
            symbol=symbol,
            symbolBrush=symbol_brushes,
            pen=pen,
            symbolSize=7,
            connect="pairs")

        # Now standalones
        test_container.draw('type1')

        symbol = ['t2', 't2']
        symbol_brushes = [pg_mock.mkBrush(test_container.color_map['type1']),
                          pg_mock.mkBrush(test_container.color_map['type1'])]
        pg_mock.PlotItem().plot().setData.assert_called_with(
            {'x': [0, 1], 'y': [0, 1]},
            symbol=symbol,
            symbolBrush=symbol_brushes,
            pen=None,
            symbolSize=7,
            connect=None)


class UIManagerTest(unittest.TestCase):
    """
    Tests the UI element creation class

    """
    def setUp(self):
        self.ui_manager = plotter._UIElementManager()

    @mock.patch("marple.display.interface.plotter.Qt")
    def test_add_elem(self, qt_mock):
        """
        Test is new_ui_elem created the right UI elements based on the input
        parameters

        """

        # Default KWargs used in the function
        callback = lambda x: x
        widget = None
        height = 100

        # Checkbox
        self.ui_manager.new_ui_elem("check", "name", "text",
                                    callback_function=callback)
        qt_mock.QtGui.QCheckBox.assert_called_once_with("text")
        qt_mock.QtGui.QCheckBox().stateChanged.connect.assert_called_once_with(
            callback)

        # Text
        self.ui_manager.new_ui_elem("text", "name", "text")
        qt_mock.QtGui.QLineEdit.assert_called_once_with("text")

        # Button
        self.ui_manager.new_ui_elem("button", "name", "text",
                                    callback_function=callback)
        qt_mock.QtGui.QPushButton.assert_called_once_with("text")
        qt_mock.QtGui.QPushButton().clicked.connect.assert_called_once_with(
            callback)

        # Group box
        self.ui_manager.new_ui_elem("group_box", "name", "text")
        qt_mock.QtGui.QGroupBox.assert_called_once_with("text")
        qt_mock.QtGui.QGroupBox().setLayout.assert_called_once()

        # Scroll area
        self.ui_manager.new_ui_elem("scroll_area", "name", "text",
                                    widget=widget, height=height)
        qt_mock.QtGui.QScrollArea.assert_called_once()
        qt_mock.QtGui.QScrollArea().setWidget.assert_called_once_with(widget)
        qt_mock.QtGui.QScrollArea().setFixedHeight.assert_called_once_with(height)

    @mock.patch("marple.display.interface.plotter.Qt")
    def test_get_elem(self, qt_mock):
        """
        Test if the function UI element getter works

        """
        self.ui_manager.new_ui_elem("check", "name", "text",
                                    callback_function=lambda x: x)
        self.assertTrue("name" in self.ui_manager.ui_dict)


# TODO: Fix the mocking of the superclass so we can test it
# class TestPlotterWindow(_BasePlotterTest):
#     def setUp(self):
#         super().setUp()
#         self.data = self.standalone_events + self.connected_events
#
#     @mock.patch("marple.display.interface.plotter.pg")
#     @mock.patch("marple.display.interface.plotter.Qt")
#     @mock.patch("marple.display.interface.plotter._EventDataProcessor")
#     @mock.patch("marple.display.interface.plotter._UIElementManager")
#     @mock.patch("marple.display.interface.plotter._PlotContainer")
#     def test_init(self, container_mock, ui_mock, processor_mock,
#                   qt_mock, pg_mock):
#         class MockGW:
#             def addLayout(self, item, row, col, rowspan, colspan):
#                 pass
#
#         with mock.patch('marple.display.interface.plotter.pg.GraphicsWindow.addLayout'):
#             window = plotter._PlotterWindow(self.data)
#         processor_mock.assert_called_once_with(self.data)
#         container_mock.assert_called_once_with(window.processed_data)
#         ui_mock.assert_called_once()
#
#         ui_mock().new_ui_elem.assert_called_with("type1_check")
#         ui_mock().new_ui_elem.assert_called_with("type2_check")
#         ui_mock().new_ui_elem.assert_called_with("regex_cpu")
#         ui_mock().new_ui_elem.assert_called_with("regex_pid")
#         ui_mock().new_ui_elem.assert_called_with("regex_comm")
#         ui_mock().new_ui_elem.assert_called_with("regex_net_ns")
#
