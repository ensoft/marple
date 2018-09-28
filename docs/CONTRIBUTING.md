# MARPLE - Multi-tool Analysis of Runtime Performance on Linux Environments
[![Build Status](https://travis-ci.org/ensoft/marple.svg?branch=master)](https://travis-ci.org/ensoft/marple)
[![Code Coverage](https://codecov.io/gh/ensoft/marple/branch/master/graph/badge.svg)](https://codecov.io/gh/ensoft/marple)
[![Pylint](https://s3-us-west-1.amazonaws.com/marple.ci.logs/most_recent/pylint.svg)](https://www.pylint.org)

## Description
MARPLE is a performance analysis and visualisation tool for Linux. It unifies a wide variety of pre-existing Linux tools such as perf and eBPF into one, simple user interface. MARPLE uses these Linux tools to collect data and write it to disk, and provides a variety of visualisation tools to display the data.

## Installation
1. Install Python 3, Perl, and Git.
~~~~
$ sudo apt-get update
$ sudo apt-get install python3 perl git
~~~~
2. Clone the MARPLE Git repository.
~~~~
$ git clone https://github.com/ensoft/marple
~~~~
3. Run the MARPLE setup script. Note that a Python virtual environment will be created at the top-level
MARPLE diretory using `venv`. This will be called `marple_env`.
~~~~
$ cd marple
$ sudo ./marple_dev_setup
~~~~
4. MARPLE is now installed, and can be run by invoking the `marple` command.
When you first use MARPLE, it will also
create a config file at `~/.marpleconfig`. Ensure that the `[g2] path` key is as follows:
~~~~
[g2]
    ...
    # Path to g2 executable
    path: <PATH TO MARPLE REPOSITORY>/vpp/build-root/install-native/g2/bin/g2
~~~~

5. You can also run MARPLE unit tests:
~~~~
$ ./marple_dev_test
~~~~

## Usage
MARPLE can be separately invoked to either collect or display data.
~~~~
usage: marple (--collect | --display) [-h] [options]
~~~~
Or alternatively:
~~~~
usage: marple (-c | -d) [-h] [options]
~~~~

### Collecting data
~~~~
usage: marple --collect [-h] [-o OUTFILE] [-t TIME]
                        subcommand [subcommand ...]

Collect performance data.

optional arguments:
  -h, --help            show this help message and exit

  subcommand            interfaces to use for data collection.

                        When multiple interfaces are specified, they will all
                        be used to collect data simultaneously.
                        Users can also define their own groups of interfaces
                        using the config file.

                        Built-in interfaces are:
                            cpusched, disklat, mallocstacks, memleak, memtime,
                            callstack, ipc, memevents, diskblockrq, perf_malloc,
                            lib
                        Current user-defined groups are:
                            boot: memleak,cpusched,disklat

  -o OUTFILE, --outfile OUTFILE
                        specify the data output file.

                        By default this will create a directory named
                        'marple_out' in the current working directory, and
                        files will be named by date and time.
                        Specifying a file name will write to the 'marple_out'
                        directory - pass in a path to override the save
                        location too.


  -t TIME, --time TIME  specify the duration for data collection (in seconds)
~~~~

The subommands are listed below. Each one collects either event-based, stack-based, or 2D point-based data.
* `cpusched`: collect CPU scheduling event-based data.
* `disklat`: collect disk latency event-based data.
* `mallocstacks`: collect `malloc()` call information (including call graph data and size of allocation) as stack-based data.
* `memleak`: collect outstanding memory allocation data (including call grap data) as stack-based data.
* `memtime`: collect data on memory usage over time as point data.
* `callstack`: collect call stack data.
* `ipc`: collect inter-process communication (IPC) data via TCP as event-based data.
* `memevents`: collect memory accesses (including call graph data) as stack-based data.
* `diskblockrq`: collect disk block accesses as event-based data.
* `perf_malloc`: collect `malloc()` call information (including call graph data) as stack-based data.
* `lib`: Not yet implemented.

MARPLE allows simultaneous collection using multiple subcommands at once - they are simply passed as multiple arguments, or as a custom collection group. Users can define custom collection groups by using the [config file](./config.txt). When using many subcommands, all data will be written to a single file.

### Displaying data
~~~~
usage: marple --display [-h] [-fg | -tm] [-g2 | -tcp] [-hm | -sp] [-i INFILE]
                        [-o OUTFILE]

Display collected data in required format

optional arguments:
  -h, --help            show this help message and exit
  -fg, --flamegraph     display as flamegraph
  -tm, --treemap        display as treemap
  -g2, --g2             display as g2 image
  -tcp, --tcpplot       display as TCP plot
  -hm, --heatmap        display as heatmap
  -sp, --stackplot      display as stackplot

  -i INFILE, --infile INFILE
                        Input file where collected data to display is stored

  -o OUTFILE, --outfile OUTFILE
                        Output file where the graph is stored
~~~~
Tree maps and flame graphs can be used to display stack-based data. G2 and the event plotter can be used to display event-based data. Heat maps and stack plots can be used to display 2D point-based data.

In general, MARPLE will not require specification of the display mode - it will determine this itself using defaults in the [config file](./config.txt). These can be overriden on a case-by-case basis using the command-line arguments. In particular, if displaying a data file with many data sets, overriding stack-based plots to display as flame graphs by using `-fg` will result in all stack-based data in that file being displayed as a flame graph for example.

Note that if collecting and displaying data on the same machine, MARPLE remembers the last data file written - in this case, no display options are necessary and simply invoking `marple -d` will give the correct display.

## Design aims
MARPLE consists of two core packages: [data collection](#the-data-collection package) and [data visualisation](#the-data-display-package). These two share some [common modules](#common-modules). Two key aims of the design are:

 * **Ease-of-use**: the user should not have to be concerned with the underlying tools used to analyse system performance. Instead, they simply specify the part of the system they would like to analyse, and MARPLE does the rest.

 * **Separation of data collection and visualisation**: the data collection module writes a data file to disk, which is later used by the visualisation module. Importantly, these two phases do not need to be run on the same machine. This allows data to be collected by one user, and sent off elsewhere for analysis by another user.

The workflow for using MARPLE is as follows:

 1. **Collect data** - specify areas of interest and duration of collection as [command line arguments](#collecting-data), and MARPLE will collect data and write it to disk.

 2. *(optional)* **Transfer collected data to another machine** - the data can be moved to another machine and still viewed.

 3. **Display data** - specify the input data file, and MARPLE will automatically select the best visualiser to display this data. Alternatively, defaults can be set in the [configuration file](#configuration) or pass as [command line arguments](#displaying-data).

## Generating docs
You can generate the MARPLE doc using if you have sphinx installed. Simply go to the `docs` folder and run `make html` in there. It can then be seen by opening `docs/build/index/html`.

## Extending MARPLE

### Adding a new collecter
To add a new collecter:
 * Implement the collecter using the `collect.interface.collecter.Collecter` interface, following the guidelines provided by the others.
 * Add info about it to the `common.consts` file (add it to everything that concerns interfaces) and `common.config` file (how to visualize it under the `DisplayInterfaces` section, and what options it has under the collecter options), where appropriate.
 * Add it as an option in the `_get_collecter_instance` function in `collect.main` file.

### Adding a new visualizer
To add a new visualizer:
 * Implement the new visualized using the `display.interface.generic_display` interface, following the guidelines provided by the others.
 * Add info about it in the `common.consts` file and the `common.config` file
 * Add it as an option in the `display.main` module arg parsing function.
