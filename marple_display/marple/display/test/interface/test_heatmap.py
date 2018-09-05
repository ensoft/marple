# -------------------------------------------------------------
# test_heatmap.py - test module for the heatmap module
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

""" Tests the heat map functionality. """

import unittest
from unittest import mock

from marple.display.interface import heatmap
from marple.common import file, data_io


class _BaseHeatMapTest(unittest.TestCase):
    """ Test class for display.heatmap module """

    # Set up test data
    def setUp(self):
        self.test_params = heatmap.GraphParameters(figure_size=10, scale=10, y_res=8)
        self.test_labels = heatmap.AxesLabels("X", "Y", "X units", "Y units")
        self.test_comps = heatmap.HeatMap._DataStats(x_min=1.0, x_max=5.0,
                                                     y_min=6.0, y_max=10.0,
                                                     y_median=8.0,
                                                     x_bins=100.0, y_bins=10.0,
                                                     x_bin_size=0.04, y_bin_size=0.4,
                                                     x_delta=4, y_delta=40)
        self.test_x_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.test_y_data = [6.0, 7.0, 8.0, 9.0, 10.0]
        self.test_data = iter(("1.0,6.0,info1\n", "2.0,7.0,info2\n",
                               "3.0,8.0,info3\n", "4.0,9.0,info4\n",
                               "5.0,10.0,info5\n"))
        self.colorbar = "Colorbar"


class GetDataTest(_BaseHeatMapTest):
    def test_empty_data(self):
        """
        Ensure HeatMap._get_data() method copes with an empty input file.

        """

        # Create blank heatmap object to access methods
        hm = object.__new__(heatmap.HeatMap)

        # Test that correct exception is raised (including message)
        with self.assertRaises(heatmap.HeatmapException) as de:
            hm._get_data(iter(()))
        err = de.exception
        self.assertEqual(str(err),
                         "Error in display.heatmap: No data in input file.")

    def test_simple_data(self):
        """
        Ensure HeatMap._get_data() method correctly converts input file.

        """
        # Create blank heatmap object to access methods
        hm = object.__new__(heatmap.HeatMap)

        # Test that correct data is produced
        x, y = hm._get_data(iter(("1.0,2.0, info1", "3.0,4.0,info2")),
                            normalised=False)
        self.assertEqual(x, [1.0, 3.0])
        self.assertEqual(y, [2.0, 4.0])

    def test_simple_time_data(self):
        """
        Ensure HeatMap._get_data() method correctly converts input file,
        with x-axis data normalisation.

        """
        # Create blank heatmap object to access methods
        hm = object.__new__(heatmap.HeatMap)

        # Test that correct data is produced
        x, y = hm._get_data(iter(("1.0,2.0, info1", "3.0,4.0,info2")),
                            normalised=True)
        self.assertEqual(x, [0.0, 2.0])
        self.assertEqual(y, [2.0, 4.0])


class GetDataStatsTest(_BaseHeatMapTest):
    def test_get_data_stats(self):
        """
        Ensure HeatMap._get_data_stats() method correctly computes measures
        from the data.

        """
        # Create blank heatmap object to access methods, set up data
        hm = object.__new__(heatmap.HeatMap)
        hm.x_data = self.test_x_data
        hm.y_data = self.test_y_data
        hm.params = self.test_params

        actual = hm._get_data_stats()
        self.assertEqual(self.test_comps, actual)


class SetAxesLimitsTest(_BaseHeatMapTest):
    def test_set_malformed_axes_limits(self):
        """
        Ensure HeatMap._set_axes_limits() copes with invalid scale/figure_size
        parameters.

        """
        # Set up test data and expected values
        test_pos = heatmap.HeatMap._ViewportPosition(0.0, 0.0)

        # Create blank heatmap object to access methods, set up data
        hm = object.__new__(heatmap.HeatMap)
        hm.data_stats = heatmap.HeatMap._DataStats(x_min=1.0, x_max=5.0,
                                                   y_min=6.0, y_max=10.0,
                                                   y_median=8.0,
                                                   x_bins=5.0, x_bin_size=0.8,
                                                   y_bins=10.0, y_bin_size=0.4,
                                                   x_delta=0.8, y_delta=0.4)
        hm.pos = test_pos

        # Ensure correct exception raised
        with self.assertRaises(heatmap.HeatmapException) as he:
            hm._set_axes_limits()
        err = he.exception
        self.assertEqual(str(err),
                         "Error in display.heatmap: Invalid axes bounds "
                         "generated - change scaling parameters.")

    def test_set_correct_axes_limits(self):
        """
        Ensure HeatMap._set_axes_limits() copes with value scale/figure_size
        parameters, and gives correct axes limits.

        """
        # Set up test data and expected values
        test_pos = heatmap.HeatMap._ViewportPosition(0.0, 0.0)

        # Create blank heatmap object to access methods, set up data
        hm = object.__new__(heatmap.HeatMap)
        hm.data_stats = self.test_comps
        hm.params = self.test_params
        hm.pos = test_pos

        # Create mock axes to record call, call _set_axes_limits()
        axes_mock = mock.Mock()
        hm.axes = axes_mock

        # Call _set_axes_limits
        hm._set_axes_limits()

        # Ensure correct calls made
        expected = [self.test_comps.x_min, self.test_comps.x_delta,
                    self.test_comps.y_min, self.test_comps.y_max]
        axes_mock.axis.assert_called_once_with(expected)


class InitTest(_BaseHeatMapTest):
    @mock.patch('marple.display.interface.heatmap.np')
    @mock.patch('marple.display.interface.heatmap.plt')
    @mock.patch('marple.display.interface.heatmap.widgets.Slider')
    def test_init(self, slider_mock, pyplot_mock, numpy_mock):
        """
        Test the __init__ method of the HeatMap class - stub out all external
        methods, and ensure correct API calls are made.
        Effectively runs through the method once, ensuring all correct values
        set and all correct calls made.

        :param read_mock:
            Mock function for the Reader class, to stub out
            filesystem interaction.
        :param slider_mock:
            Mock class for the matplotlib.widgets.Slider class.
        :param pyplot_mock:
            Mock class for the matplotlib.pyplot package
        :param numpy_mock:
            Mock class for the numpy package.

        """
        # Create pyplot mocks
        axes_mock = pyplot_mock.gca.return_value
        fig_mock = pyplot_mock.gcf.return_value
        image_mock = axes_mock.imshow.return_value
        xslide_mock, yslide_mock = mock.MagicMock(), mock.MagicMock()
        pyplot_mock.axes.side_effect = [xslide_mock, yslide_mock]

        # Create numpy mocks
        median_item = mock.MagicMock()
        median_item.item.return_value = 8.0
        numpy_mock.median.return_value = median_item
        hm_mock, xedges_mock, yedges_mock = \
            mock.MagicMock(), mock.MagicMock(), mock.MagicMock()
        numpy_mock.histogram2d.return_value = \
            (hm_mock, xedges_mock, yedges_mock)

        # Create slider mocks
        xslide_pos_mock, yslide_pos_mock = mock.MagicMock(), mock.MagicMock()
        slider_mock.side_effect = [xslide_pos_mock, yslide_pos_mock]

        # RUN TRHOUGH INIT - CHECK VALUES/FUNCTION CALLS ARE AS EXPECTED
        # Mock out file
        out = file.DisplayFileName()
        hm = heatmap.HeatMap(self.test_data, out,
                             data_io.PointData.DataOptions('X', 'Y',
                                                             'X units',
                                                             'Y units'),
                             heatmap.HeatMap.DisplayOptions(self.colorbar,
                                                            self.test_params,
                                                            False))

        # Check field values
        self.assertEqual(hm.labels, self.test_labels)
        self.assertEqual(hm.params, self.test_params)

        # Check _get_data()
        self.assertEqual(hm.x_data, self.test_x_data)
        self.assertEqual(hm.y_data, self.test_y_data)

        # Check _get_data_stats()
        self.assertEqual(hm.data_stats, self.test_comps)

        # Check _create_axes()
        fig_mock.canvas.set_window_title.assert_called_once_with("Heat map")
        pyplot_mock.xlabel.assert_called_once_with(
            self.test_labels.x + ' / ' + self.test_labels.x_units, va="top")
        pyplot_mock.ylabel.assert_called_once_with(
            self.test_labels.y + ' / ' + self.test_labels.y_units, rotation=90,
            va="bottom")
        fig_mock.set_size_inches.assert_called_once_with(
            self.test_params.figure_size, self.test_params.figure_size,
            forward=True)
        self.assertEqual(axes_mock, hm.axes)
        self.assertEqual(fig_mock, hm.figure)

        # Check _plot_histogram()
        numpy_mock.histogram2d.assert_called_once_with(
            self.test_x_data, self.test_y_data, bins=(self.test_comps.x_bins,
                                                      self.test_comps.y_bins))
        axes_mock.imshow.assert_called_once_with(
            hm_mock.T, cmap="OrRd",
            extent=[xedges_mock[0], xedges_mock[-1],
                    yedges_mock[0], yedges_mock[-1]],
            origin="lower", aspect="auto")
        self.assertEqual(hm_mock, hm.heatmap)
        self.assertEqual(image_mock, hm.image)

        # Check viewport position
        self.assertEqual(hm.pos, heatmap.HeatMap._ViewportPosition(
             self.test_comps.x_delta, self.test_comps.y_delta))

        # Check _set_axes_limits()
        expected = [self.test_comps.x_min, self.test_comps.x_max,
                    self.test_comps.y_min, self.test_comps.y_max]
        axes_mock.axis.assert_called_once_with(expected)

        # Check _add_colorbar()
        axes_mock.figure.colorbar.assert_called_once_with(image_mock,
                                                          ax=axes_mock)
        cbar_mock = axes_mock.figure.colorbar.return_value
        cbar_mock.ax.set_ylabel.assert_called_once_with(
            self.colorbar)

        # Check _create_sliders()
        axes_calls = [mock.call([0.2, 0.95, 0.6, 0.015]),
                 mock.call([0.2, 0.9, 0.6, 0.015])]
        pyplot_mock.axes.assert_has_calls(axes_calls)
        slider_calls = [
            mock.call(xslide_mock,
                      'Position of x-axis\n/ ' + self.test_labels.x_units,
                      self.test_comps.x_min + self.test_comps.x_delta,
                      self.test_comps.x_max - self.test_comps.x_delta),
            mock.call(yslide_mock,
                      'Position of y-axis\n/ ' + self.test_labels.y_units,
                      self.test_comps.y_min + self.test_comps.y_delta,
                      self.test_comps.y_max - self.test_comps.y_delta)]
        slider_mock.assert_has_calls(slider_calls)
        xslide_pos_mock.valtext.set_visible.assert_called_once_with(False)
        yslide_pos_mock.valtext.set_visible.assert_called_once_with(False)
        xslide_pos_mock.on_changed.assert_called_once()
        yslide_pos_mock.on_changed.assert_called_once()

        # Check _add_annotations()
        axes_mock.annotate.assert_called_once_with(
            "", xy=(0, 0), xytext=(5, 7), xycoords="data",
            textcoords="offset points", bbox=dict(boxstyle="square"))
        annot_mock = axes_mock.annotate.return_value
        annot_mock.set_visible.assert_called_once_with(False)
        fig_mock.canvas.mpl_connect.assert_called_once()
