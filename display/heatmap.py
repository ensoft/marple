# -------------------------------------------------------------
# heatmap.py - creates a heat map from a data file.
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

"""
    Heat map functionality from a data file.

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
    'DEFAULT_PARAMETERS',
    'HeatMap',
    'HeatMap.show',
    'HeatMap.save'
)

import math
from typing import NamedTuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

from common.datatypes import Datapoint

# @@@ TODO save interactive files (see pickle package)
# @@@ TODO scroll to zoom
# @@@ TODO add extra dataset for display in annotation
#     (e.g. PID of processes in current bin)


class AxesLabels(NamedTuple):
    """
    Class for storing labellings for heat map axes.

    x:
        Label for x-axis.
    y:
        Label for y-axis.
    x_units:
        Units for the x-axis.
    y_units:
        Units for the y-axis.
    colorbar:
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

    figure_size:
        The size of the square figure on-screen, in inches.
    scale:
        The scale of the graph - larger means more histogram bins
        (i.e. more zoomed in)
    y_res:
        The resolution on the y-axis - larger means greater resolution.

    """
    figure_size: float
    scale: float
    y_res: float


DEFAULT_PARAMETERS = GraphParameters(figure_size=10.0, scale=5.0, y_res=10.0)


class HeatMap:
    """
    The :class:`HeatMap` constructor takes in the input data file,
    a :class:`AxesLabels` object, and a :class:`GraphParameters` object.
    It creates the heat map with a colourbar, scrollable axes, and annotations
    on hover.

    To show the heat map, use :func:`HeatMap.show`.
    To save, use :func:`HeatMap.save`.

    """
    def __init__(self, datafile, labels,
                 parameters=DEFAULT_PARAMETERS):
        # Set parameters
        self.labels = labels
        self.params = parameters

        # Get data
        self.x_data, self.y_data = self._get_data(datafile)

        # Get values calculated from data
        self.comps = self._get_data_comps()

        # Plot
        self.axes, self.figure = self._create_axes()
        self.heatmap, self.image = self._plot_histogram()

        # Set current viewport
        self.pos = self._ViewportPosition(self.comps.x_delta,
                                          self.comps.y_delta)

        # Set current axes
        self._set_axes_limits()

        # Add features - colorbar, sliders, annotations
        self._add_colorbar()

        self._create_sliders()

        self._add_annotations()

    # The two methods below are not static as we would like a HeatMap instance
    # to be created before they are used.
    def save(self, outputfile):
        """
        Save the heat map to disk.
        This will fail if the file is not of the correct format.

        :param outputfile:
            The output file name.
        """
        plt.savefig(outputfile, bbox_inches="tight")

    def show(self):
        plt.show()

    class _DataComps(NamedTuple):
        """
        Internal class for storing values computed from the data.

        x_min, x_max:
            Minimum and maximum x-axis datapoints.
        y_min, y_max:
            Minimum and maximum y-axis datapoints.
        y_median:
            Median y-axis datapoint, for calculating scaling of y-axis.
        x_bins, x_bin_size:
            The number of bins on the x-axis, and their size.
        y_bins, y_bin_size:
            The number of bins on the y-axis, and their size.
        x_delta, y_delta:
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

        x:
            Position in x-axis.
        y:
            Position in y-axis.

        """
        x: float
        y: float

    def _get_data(self, datafile, time=True):
        """
        Gets heatmap data from a data file.

        File is generated from writing :class:`Datapoint` objects to strings,
        one on each line.

        :param time:
            True if x values should be normalised to start from zero.
        :return:
            A pair of sequences: x values, y values.

        """
        with open(datafile, "r") as file:
            # Get data
            datapoints = [Datapoint.from_string(line) for line in file]

            x_values = [dp.x for dp in datapoints]
            y_values = [dp.y for dp in datapoints]

            if time:
                # Normalize x-axis values to start from zero
                x_values = [x - min(x_values) for x in x_values]

        return x_values, y_values

    def _create_axes(self):
        """
        Create axes and figure objects ready for use.

        :return:
            A pair consisting of: axes, figure.

        """
        # Get axes and figure
        axes = plt.gca()
        fig = plt.gcf()
        fig.canvas.set_window_title('Heat map')

        # Set axis labels
        plt.xlabel(self.labels.x+' / '+self.labels.x_units, va="top")
        plt.ylabel(self.labels.y+' / '+self.labels.y_units,
                   rotation=90, va="bottom")

        # Set figure size
        fig.set_size_inches(self.params.figure_size, self.params.figure_size,
                            forward=True)

        return axes, fig

    def _get_data_comps(self):
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

        return self._DataComps(x_min=x_min, x_max=x_max, y_min=y_min,
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
                                                 bins=(self.comps.x_bins,
                                                       self.comps.y_bins))
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

        # Plot data
        image = self.axes.imshow(heatmap.T, cmap='OrRd', extent=extent,
                                 origin='lower', aspect='auto')

        return heatmap, image

    def _set_axes_limits(self):
        """
        Set the limits of the axes that should be visible.

        """
        x_ax_min = max(self.comps.x_min, self.pos.x - self.comps.x_delta)
        x_ax_max = min(self.comps.x_max, self.pos.x + self.comps.x_delta)
        y_ax_min = max(self.comps.y_min, self.pos.y - self.comps.y_delta)
        y_ax_max = min(self.comps.y_max, self.pos.y + self.comps.y_delta)

        self.axes.axis([x_ax_min, x_ax_max, y_ax_min, y_ax_max])

    def _redraw(self):
        """ Redraw the graph """
        self.figure.canvas.draw_idle()

    def _create_sliders(self):
        """ Create sliders that allow the user to scroll the axes. """
        # Create sliders for scrollable axes
        x_slider = plt.axes([0.2, 0.95, 0.6, 0.015])
        x_slider_pos = Slider(x_slider,
                              'Position of x-axis\n/ '+self.labels.x_units,
                              self.comps.x_min + self.comps.x_delta,
                              self.comps.x_max - self.comps.x_delta)
        x_slider_pos.valtext.set_visible(False)

        y_slider = plt.axes([0.2, 0.9, 0.6, 0.015])
        y_slider_pos = Slider(y_slider,
                              'Position of y-axis\n/ '+self.labels.y_units,
                              self.comps.y_min + self.comps.y_delta,
                              self.comps.y_max - self.comps.y_delta)
        y_slider_pos.valtext.set_visible(False)

        def update(val):
            """ Update the axes on slider change """
            # Determine new positions
            self.pos = self._ViewportPosition(x=x_slider_pos.val,
                                              y=y_slider_pos.val)
            self._set_axes_limits()

            # Redraw
            self._redraw()

        # Listeners for slider changes
        x_slider_pos.on_changed(update)
        y_slider_pos.on_changed(update)

    def _add_colorbar(self):
        """ Add a colorbar scale to the graph. """
        colorbar = self.axes.figure.colorbar(self.image, ax=self.axes)
        colorbar.ax.set_ylabel(self.labels.colorbar)

    def _add_annotations(self):
        """ Add hovering annotations to the graph. """
        annot = self.axes.annotate("", xy=(0, 0), xytext=(5, 7),
                                   xycoords="data", textcoords="offset points",
                                   bbox=dict(boxstyle="square"))

        annot.set_visible(False)

        def hover(event):
            """ Update the figure on hover. """
            if event.inaxes == self.axes:
                x_bin = int(math.floor((event.xdata - self.comps.x_min) /
                                       self.comps.x_bin_size))
                y_bin = int(math.floor((event.ydata - self.comps.y_min) /
                                       self.comps.y_bin_size))
                text = "Bin (x-axis): {:.2g} - {:.2g} units\n" \
                       "Bin (y-axis): {:.4g} - {:.4g} units\n" \
                       "Count: {}".format(x_bin, x_bin + self.comps.x_bin_size,
                                          y_bin, y_bin + self.comps.y_bin_size,
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
