# -------------------------------------------------------------
# heatmap.py - creates and displays a heat map.
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

"""
Creating and displaying heat maps.

The data file should be comma-separated 2D datapoints with accompanying
information or annotation: <x>,<y>,<info>.

Two classes are provided for modifying the graph:
    :class:`AxesLabels` allows labelling of axes.
    :class:`GraphParameters` allows scaling.

The class :class:`HeatMap` encapsulates the heat map itself,
and allows construction, display, and saving of the figure.

"""

__all__ = (
    'AxesLabels',
    'GraphParameters',
    'HeatmapException',
    'HeatMap',
)

import logging
import math
from typing import NamedTuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import widgets

from common import util
from common import datatypes

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


# @@@ TODO save interactive files (see pickle package)
# @@@ TODO scroll to zoom
# @@@ TODO add extra dataset for display in annotation
#     (e.g. PID of processes in current bin)


class AxesLabels(NamedTuple):
    """
    Class for storing labellings for heat map axes.

    .. atrribute:: x:
        Label for x-axis.
    .. atrribute:: y:
        Label for y-axis.
    .. atrribute:: x_units:
        Units for the x-axis.
    .. atrribute:: y_units:
        Units for the y-axis.
    .. atrribute:: colorbar:
        Label for the colourbar.

    """
    x: str
    y: str
    x_units: str
    y_units: str
    colorbar: str


class GraphParameters(NamedTuple):
    """
    Class for storing heatmap graph display parameters.

    .. atrribute:: figure_size:
        The size of the square figure on-screen, in inches.
    .. atrribute:: scale:
        The scale of the graph - larger means more histogram bins
        (i.e. more zoomed in)
    .. atrribute:: y_res:
        The resolution on the y-axis - larger means greater resolution.

    """
    figure_size: float
    scale: float
    y_res: float


class HeatmapException(Exception):
    def __init__(self, msg):
        super().__init__("Error in display.heatmap: " + msg)


# Default parameters - the graph is 10 x 10 inches on screen, with a scale
# factor of 5, and a y-axis resolution of 10 (10 histogram bins will be
# visible below the median y-value.
DEFAULT_PARAMETERS = GraphParameters(figure_size=10.0, scale=5.0, y_res=10.0)


class HeatMap:
    """
    The core class for creating and displaying heat maps.

    The :class:`HeatMap` constructor takes in the input data file,
    a :class:`AxesLabels` object, and a :class:`GraphParameters` object.
    It creates the heat map with a colourbar, scrollable axes, and annotations
    on hover.

    To show the heat map, use :func:`HeatMap.show`.
    To save, use :func:`HeatMap.save`.

    """

    def __init__(self, datafile, labels,
                 parameters=DEFAULT_PARAMETERS, normalise=True):
        """
        Constructor for the heat map - initialises the heatmap.

        :param datafile:
            The input data file.
        :param labels:
            An object of :class:`AxesLabels`, storing labels for the heat map.
        :param parameters:
            An object of :class `GraphParameters`, storing parameters for
            displaying the graph.
        :param normalise:
            True if the x-axis should be normalised to start from zero.

        """
        self.labels = labels
        self.params = parameters
        self.x_data, self.y_data = self._get_data(datafile, normalise)

        # Get values calculated from data
        self.data_stats = self._get_data_stats()

        # Plot, set viewport, set axes limits
        self.axes, self.figure = self._create_axes()
        self.heatmap, self.image = self._plot_histogram()
        self.pos = self._ViewportPosition(self.data_stats.x_delta,
                                          self.data_stats.y_delta)
        self._set_axes_limits()

        # Add features - colorbar, sliders, annotations
        self._add_colorbar()
        self._create_sliders()
        self._add_annotations()

    # The two methods below are not class/static methods as we would like a
    # HeatMap instance to be created before they are used.
    @util.log(logger)
    def save(self, outputfile):
        """
        Save the heat map to disk.
        This will fail if the file is not of the correct format.

        :param outputfile:
            The output file name.
        """
        plt.savefig(outputfile, bbox_inches="tight")

    @util.log(logger)
    def show(self):
        plt.show()

    class _DataStats(NamedTuple):
        """
        Internal class for storing values computed from the data.

        .. atrribute:: x_min, x_max:
            Minimum and maximum x-axis datapoints.
        .. atrribute:: y_min, y_max:
            Minimum and maximum y-axis datapoints.
        .. atrribute:: y_median:
            Median y-axis datapoint, for calculating scaling of y-axis.
        .. atrribute:: x_bins, x_bin_size:
            The number of bins on the x-axis, and their size.
        .. atrribute:: y_bins, y_bin_size:
            The number of bins on the y-axis, and their size.
        .. atrribute:: x_delta, y_delta:
            Delta values for x-axis and y-axis respectively.
            These are useful values for calculating
            how much of the graph should be visible.
            In general, 2 * delta will be visible on each axis.

        """
        x_min: float
        y_min: float
        x_max: float
        y_max: float
        y_median: float
        x_bins: float
        x_bin_size: float
        y_bins: float
        y_bin_size: float
        x_delta: float
        y_delta: float

    class _ViewportPosition(NamedTuple):
        """
        Internal class for storing position of current viewport.

        .. atrribute:: x:
            Position in x-axis.
        .. atrribute:: y:
            Position in y-axis.

        """
        x: float
        y: float

    @util.log(logger)
    def _get_data(self, datafile, normalised=True):
        """
        Gets heatmap data from a data file.

        File is generated from writing :class:`Datapoint` objects to strings,
        one on each line.

        :param datafile:
            The input data file.
        :param normalised:
            True if x values should be normalised to start from zero.

        :return:
            A pair of sequences: x values, y values.

        """
        with open(datafile, "r") as file:
            # Get data
            datapoints = [datatypes.Datapoint.from_string(line)
                          for line in file]

        x_values = [dp.x for dp in datapoints]
        y_values = [dp.y for dp in datapoints]

        if not x_values or not y_values:
            raise HeatmapException("No data in input file.")
        if normalised:
            # Normalize x-axis values to start from zero
            x_values = [x - min(x_values) for x in x_values]

        return x_values, y_values

    def _create_axes(self):
        """
        Create axes and figure objects ready for use.

        The axes object is of type :class:`matplotlib.axes.Axes`.
        The figure object is of type :class:`matplotlib.figure.Figure`

        :return:
            A pair consisting of: axes, figure.

        """
        # Get axes and figure
        axes = plt.gca()
        fig = plt.gcf()
        fig.canvas.set_window_title('Heat map')

        # Set axis labels
        plt.xlabel(self.labels.x + ' / ' + self.labels.x_units, va="top")
        plt.ylabel(self.labels.y + ' / ' + self.labels.y_units,
                   rotation=90, va="bottom")

        # Set figure size
        fig.set_size_inches(self.params.figure_size, self.params.figure_size,
                            forward=True)

        return axes, fig

    def _get_data_stats(self):
        """
        Determine values computed from the data.

        :return:
            An object of class :class:`_DataComps`

        """
        # Determine minimum, maximum, median
        x_min, x_max = min(self.x_data), max(self.x_data)
        y_min, y_max = min(self.y_data), max(self.y_data)
        y_med = np.median(self.y_data).item()

        # Determine no. bins and bin size
        x_bins = max(self.params.scale * self.params.figure_size, x_max)
        y_bins = y_max / (y_med / self.params.y_res)
        x_bin_size = (x_max - x_min) / x_bins
        y_bin_size = (y_max - y_min) / y_bins

        # Get delta values
        x_delta = self.params.scale * self.params.figure_size * x_bin_size
        y_delta = self.params.scale * self.params.figure_size * y_bin_size

        return self._DataStats(x_min=x_min, x_max=x_max, y_min=y_min,
                               y_max=y_max, y_median=y_med, x_bins=x_bins,
                               y_bins=y_bins, x_bin_size=x_bin_size,
                               y_bin_size=y_bin_size, x_delta=x_delta,
                               y_delta=y_delta)

    def _plot_histogram(self):
        """
        Plot the histogram.

        :return:
            The resulting heat map and the resulting AxesImage.

        """
        # Get histogram
        heatmap, xedges, yedges = np.histogram2d(self.x_data, self.y_data,
                                                 bins=(self.data_stats.x_bins,
                                                       self.data_stats.y_bins))
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

        # Plot data - use OrRd (OrangeRed colour scheme)
        # heatmap.T transposes the heatmap ndarray
        image = self.axes.imshow(heatmap.T, cmap='OrRd', extent=extent,
                                 origin='lower', aspect='auto')

        return heatmap, image

    def _set_axes_limits(self):
        """
        Set the limits of the axes that should be visible.

        """
        x_ax_min = max(self.data_stats.x_min, self.pos.x - self.data_stats.x_delta)
        x_ax_max = min(self.data_stats.x_max, self.pos.x + self.data_stats.x_delta)
        y_ax_min = max(self.data_stats.y_min, self.pos.y - self.data_stats.y_delta)
        y_ax_max = min(self.data_stats.y_max, self.pos.y + self.data_stats.y_delta)

        if x_ax_min >= x_ax_max or y_ax_min >= y_ax_max:
            raise HeatmapException("Invalid axes bounds generated - change "
                                   "scaling parameters.")

        self.axes.axis([x_ax_min, x_ax_max, y_ax_min, y_ax_max])

    def _redraw(self):
        """ Redraw the graph """
        self.figure.canvas.draw_idle()

    def _create_sliders(self):
        """ Create sliders that allow the user to scroll the axes. """
        # Create sliders for scrollable axes
        # Position at top of the graph - numbers below are positionings relative
        # to the figure: [left, bottom, width, height]
        x_slider = plt.axes([0.2, 0.95, 0.6, 0.015])
        x_slider_pos = widgets.Slider(x_slider,
                              'Position of x-axis\n/ ' + self.labels.x_units,
                              self.data_stats.x_min + self.data_stats.x_delta,
                              self.data_stats.x_max - self.data_stats.x_delta)
        x_slider_pos.valtext.set_visible(False)

        y_slider = plt.axes([0.2, 0.9, 0.6, 0.015])
        y_slider_pos = widgets.Slider(y_slider,
                              'Position of y-axis\n/ ' + self.labels.y_units,
                              self.data_stats.y_min + self.data_stats.y_delta,
                              self.data_stats.y_max - self.data_stats.y_delta)
        y_slider_pos.valtext.set_visible(False)

        def update(val):
            """ Update the axes on slider change """
            # Determine new positions
            self.pos = self._ViewportPosition(x=x_slider_pos.val,
                                              y=y_slider_pos.val)
            self._set_axes_limits()
            self._redraw()

        # Listeners for slider changes
        x_slider_pos.on_changed(update)
        y_slider_pos.on_changed(update)

    def _add_colorbar(self):
        """ Add a colorbar scale to the graph. """
        colorbar = self.axes.figure.colorbar(self.image, ax=self.axes)
        colorbar.ax.set_ylabel(self.labels.colorbar)

    def _add_annotations(self):
        """
        Add hovering annotations to the graph.

        The annotations contain information on the current bin under the cursor,
        and the count of entries in that bin.

        """
        # xy=(0, 0) is the inital annotation position (in data units)
        # xytext=(5,7) is the constant offset of the annotation display
        annot = self.axes.annotate("", xy=(0, 0), xytext=(5, 7),
                                   xycoords="data", textcoords="offset points",
                                   bbox=dict(boxstyle="square"))

        annot.set_visible(False)

        def hover(event):
            """ Update the figure on hover. """
            # Check if mouse is within axes
            if event.inaxes == self.axes:
                # Compute which bins we are in
                x_bin = int(math.floor((event.xdata - self.data_stats.x_min) /
                                       self.data_stats.x_bin_size))
                y_bin = int(math.floor((event.ydata - self.data_stats.y_min) /
                                       self.data_stats.y_bin_size))

                # Update annotation text to reflect
                text = "Bin (x-axis): {:.2g} - {:.2g} units\n" \
                       "Bin (y-axis): {:.4g} - {:.4g} units\n" \
                       "Count: {}".format(x_bin,
                                          x_bin + self.data_stats.x_bin_size,
                                          y_bin,
                                          y_bin + self.data_stats.y_bin_size,
                                          self.heatmap[x_bin, y_bin])
                annot.xy = (event.xdata, event.ydata)
                annot.set_text(text)
                annot.get_bbox_patch().set_alpha(0.4)
                annot.set_visible(True)
                self._redraw()
            else:
                annot.set_visible(False)
                self._redraw()

        self.figure.canvas.mpl_connect("motion_notify_event", hover)
