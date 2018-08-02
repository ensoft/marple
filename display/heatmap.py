import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import math

# @@@ TODO save interactive files (see pickle package)
# @@@ TODO scroll to zoom
# @@@ TODO add extra dataset for display in annotation
#     (e.g. PID of processes in current bin)


class HeatMap:
    HEADER_SIZE = 8

    def __init__(self, datafile, outputfile, labels,
                 figure_size=10, scale=5, y_res=10):
        # Create input/output filenames
        self.datafile = datafile
        self.outputfile = outputfile

        # Set parameters
        self.labels = labels
        self.figure_size = figure_size
        self.scale = scale
        self.y_res = y_res

        """
        The following variables are defined above:
        labels:
            Labels for the axes (with units), and label for the colorbar.
            A dictionary with the following fields:
                "X_LAB", "Y_LAB", "X_UNITS", "Y_UNITS", "COLORBAR"
        figure_size:
            The size of the graph in inches.
        scale:
            A scale factor for the graph: larger scale gives a more zoomed out
            graph.
        y_res:
            The resolution of the y-axis: a larger value gives finer bins.

        """

        # Get data
        self.x_data, self.y_data = self.get_data()
        self.bounds = self.data_bounds()
        self.bins = self.data_bins()
        self.delta = self.get_delta()
        """
        The following data attributes are defined above:
            x_data, y_data:
                The data itself.
            bounds:
                Maximum and minimum values, and median y value.
            bins:
                Number of histogram bins and their sizes.
            delta:
                Useful variables for resizing axes.
                In general, the visible axes will span two deltas.

        """

        # Plot
        self.axes, self.figure = self.create_axes()
        self.heatmap, self.image = self.plot_histogram()

        # Set initial axes
        self.pos = dict(X=self.delta['X'], Y=self.delta['Y'])
        # pos: position of current viewport
        self.set_axes_limits()

        # Add features - colorbar, sliders, annotations
        self.add_colorbar()
        self.create_sliders()
        self.add_annotations()

    # def parse_header(self):
    #     """
    #     Parse the header of the data file to set graph parameters.
    #     The header should be as follows:
    #         <figure size>
    #         <figure scale>
    #         <y-axis resolution>
    #         <x-axis label>
    #         <x-axis units>
    #         <y-axis label>
    #         <y-axis units>
    #         <colourbar label>
    #
    #     :return:
    #         A tuple consisting of figure size, graph scale, y-axis resolution,
    #         and a dictionary of axis labels.
    #
    #     """
    #     with open(self.datafile, "r") as file:
    #         figure_size = int(file.readline())
    #         scale = int(file.readline())
    #         y_res = int(file.readline())
    #         x_lab = file.readline().strip()
    #         x_unit = file.readline().strip()
    #         y_lab = file.readline().strip()
    #         y_unit = file.readline().strip()
    #         cbar_lab = file.readline().strip()
    #         labels = dict(X_LAB=x_lab, X_UNITS=x_unit, Y_LAB=y_lab,
    #                       Y_UNITS=y_unit, COLORBAR=cbar_lab)
    #         return figure_size, scale, y_res, labels

    def get_data(self, time=True):
        """
        Gets heatmap data from a data file.

        File is assumed to be two columns of values "x y".
        Assume that x values are time, so they are normalised to
        start from zero.

        :param time:
            True if x values are time, and so should be normalised.
        :return:
            A pair of sequences: x values, y values.

        """
        with open(self.datafile, "r") as file:
            # # Skip header
            # for _ in range(HeatMap.HEADER_SIZE):
            #     next(file)

            # Get data
            xy_values = [(float(line.split()[0]),
                         float(line.split()[1]))
                         for line in file]

            x_values = [x for (x, _) in xy_values]
            y_values = [y for (_, y) in xy_values]

            if time:
                # Normalize x-axis values to start from zero
                x_values = [x - min(x_values) for x in x_values]

            return x_values, y_values

    def create_axes(self):
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
        plt.xlabel(self.labels['X_LAB']+' / '+self.labels['X_UNITS'], va="top")
        plt.ylabel(self.labels['Y_LAB']+' / '+self.labels['Y_UNITS'],
                   rotation=90, va="bottom")

        # Set figure size
        fig.set_size_inches(self.figure_size, self.figure_size, forward=True)

        return axes, fig

    def data_bounds(self):
        """
        Determine the upper/lower bounds of the data.

        :return:
            A dictionary containing the bounds, and the median y value.

        """
        return dict(X_MIN=min(self.x_data), X_MAX=max(self.x_data),
                    Y_MIN=min(self.y_data), Y_MAX=max(self.y_data),
                    Y_MEDIAN=np.median(self.y_data))

    def data_bins(self):
        """
        Determine the number of bins for the histogram.

        :return:
            A dictionary containing the number of bins and their size
            for both sets of data.

        """
        # Determine no. of bins
        x_bins = max(self.scale * self.figure_size, self.bounds['X_MAX'])
        # i.e. minimum of SCALE * FIGURE_SIZE bins, up to a bin for every second
        y_bins = self.bounds['Y_MAX'] / (self.bounds['Y_MEDIAN'] / self.y_res)
        # i.e. enough bins to alllow resolution of Y_RES bins below median

        # Determine bin sizes
        x_bin_size = (self.bounds['X_MAX'] - self.bounds['X_MIN']) / x_bins
        y_bin_size = (self.bounds['Y_MAX'] - self.bounds['Y_MIN']) / y_bins

        return dict(X_BINS=x_bins, Y_BINS=y_bins,
                    X_SIZE=x_bin_size, Y_SIZE=y_bin_size)

    def get_delta(self):
        """
        Get the deltas - useful variables for adjusting axes.
        The visible axes should in general span two deltas.

        :return:
            A dictionary containing the delta measures, useful for calculating
            which parts of the axes should be visible

        """
        x_delta = self.scale * self.figure_size * self.bins['X_SIZE']
        y_delta = self.scale * self.figure_size * self.bins['Y_SIZE']

        return dict(X=x_delta, Y=y_delta)

    def plot_histogram(self):
        """
        Plot the histogram.

        :return:
            The resulting heat map and the resulting AxesImage.

        """
        # Get histogram
        heatmap, xedges, yedges = np.histogram2d(self.x_data, self.y_data,
                                                 bins=(self.bins['X_BINS'],
                                                       self.bins['Y_BINS']))
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

        # Plot data
        image = self.axes.imshow(heatmap.T, cmap='OrRd', extent=extent,
                                 origin='lower', aspect='auto')

        return heatmap, image

    def set_axes_limits(self):
        """
        Set the limits of the axes that should be visible.

        """
        x_ax_min = max(self.bounds['X_MIN'], self.pos['X'] - self.delta['X'])
        x_ax_max = min(self.bounds['X_MAX'], self.pos['X'] + self.delta['X'])
        y_ax_min = max(self.bounds['Y_MIN'], self.pos['Y'] - self.delta['Y'])
        y_ax_max = min(self.bounds['Y_MAX'], self.pos['Y'] + self.delta['Y'])

        self.axes.axis([x_ax_min, x_ax_max, y_ax_min, y_ax_max])

    def redraw(self):
        """ Redraw the graph """
        self.figure.canvas.draw_idle()

    def create_sliders(self):
        """ Create sliders that allow the user to scroll the axes. """
        # Create sliders for scrollable axes
        x_slider = plt.axes([0.2, 0.95, 0.6, 0.015])
        x_slider_pos = Slider(x_slider,
                              'Position of x-axis\n/ '+self.labels['X_UNITS'],
                              self.bounds['X_MIN'] + self.delta['X'],
                              self.bounds['X_MAX'] - self.delta['X'])

        y_slider = plt.axes([0.2, 0.9, 0.6, 0.015])
        y_slider_pos = Slider(y_slider,
                              'Position of y-axis\n/ '+self.labels['Y_UNITS'],
                              self.bounds['Y_MIN'] + self.delta['Y'],
                              self.bounds['Y_MAX'] - self.delta['Y'])

        def update(val):
            """ Update the axes on slider change """
            # Determine new positions
            self.pos = dict(X=x_slider_pos.val, Y=y_slider_pos.val)
            self.set_axes_limits()

            # Redraw
            self.redraw()

        # Listeners for slider changes
        x_slider_pos.on_changed(update)
        y_slider_pos.on_changed(update)

    def add_colorbar(self):
        """ Add a colorbar scale to the graph. """
        colorbar = self.axes.figure.colorbar(self.image, ax=self.axes)
        colorbar.ax.set_ylabel(self.labels['COLORBAR'])

    def add_annotations(self):
        """ Add hovering annotations to the graph. """
        annot = self.axes.annotate("", xy=(0, 0), xytext=(5, 7),
                                   xycoords="data", textcoords="offset points",
                                   bbox=dict(boxstyle="square"))

        annot.set_visible(False)

        def hover(event):
            """ Update the figure on hover. """
            if event.inaxes == self.axes:
                x_bin = int(math.floor(event.xdata / self.bins['X_SIZE']))
                y_bin = int(math.floor(event.ydata / self.bins['Y_SIZE']))
                text = "Bin (x-axis): {:.2g} - {:.2g} units\n" \
                       "Bin (y-axis): {:.4g} - {:.4g} units\n" \
                       "Count: {}".format(x_bin, x_bin + self.bins['X_SIZE'],
                                          y_bin, y_bin + self.bins['Y_SIZE'],
                                          self.heatmap[x_bin, y_bin])
                annot.xy = (event.xdata, event.ydata)
                annot.set_text(text)
                annot.get_bbox_patch().set_alpha(0.4)
                annot.set_visible(True)
                self.redraw()
            else:
                annot.set_visible(False)
                self.redraw()

        self.figure.canvas.mpl_connect("motion_notify_event", hover)

    def save(self):
        """ Save the file to output. @@@ TODO save interactivity too """
        plt.savefig(self.outputfile, bbox_inches="tight")

    @classmethod
    def show(cls):
        plt.show()
