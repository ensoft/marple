# MARPLE - Multi-tool Analysis of Runtime Performance on Linux Environments
[![Build Status](https://travis-ci.org/ensoft/marple.svg?branch=master)](https://travis-ci.org/ensoft/marple)
[![Code Coverage](https://codecov.io/gh/ensoft/marple/branch/master/graph/badge.svg)](https://codecov.io/gh/ensoft/marple)
[![Pylint](https://s3-us-west-1.amazonaws.com/marple.ci.logs/most_recent/pylint.svg)](https://www.pylint.org)

## Description
MARPLE is a performance analysis and visualisation tool for Linux. It unifies a wide variety of pre-existing Linux tools such as perf and eBPF into one, simple user interface. MARPLE uses these Linux tools to collect data and write it to disk, and provides a variety of visualisation tools to display the data. The software is open-source, and can be found on our [GitHub repository](https://github.com/ensoft/marple).

## Installation
1. Install Python 3 and Perl.
~~~~
$ sudo apt-get update
$ sudo apt-get install python3 perl
~~~~
2. Clone the MARPLE Git repository.
~~~~
$ git clone https://github.com/ensoft/marple
~~~~
3. Run the MARPLE setup script.
~~~~
$ cd marple
$ sudo ./setup
~~~~
4. MARPLE is now installed, and can be run by invoking the `marple` command, as described in [the usage section.](#usage)

## Usage
As described in [the design section](#design), MARPLE can be separately invoked to either collect or display data. Usage:
~~~~
marple {collect | display} <options>
~~~~

### Collecting data
Usage:
~~~~
marple collect <options>

optional arguments:
TODO
~~~~

### Displaying data
Usage:
~~~~
marple display [-i infile] [-o outfile] [-l] [-fg | -tm | -hm | -sp]

optional arguments:
  -i, --infile: the filename of the input data
  -o, --outfile: the output filename
  -fg: display the data as a flamegraph
  -tm: display the data as a treemap
  -hm: display the data as a heatmap
  -sp: display the data as a stackplot
~~~~

## Design
MARPLE consists of two core packages: [data collection](#the-data-collection package) (`collect`) and [data visualisation](#the-data-display-package) (`display`). These two share some [common modules](#common-modules) (`common`) for file handling and so on (see [the design diagram](#marple_design)). Two key aims of this design are:

 * **Ease-of-use**: the user should not have to be concerned with the underlying tools used to analyse system performance. Instead, they simply specify the part of the system they would like to analyse, and MARPLE does the rest.

 * **Separation of data collection and visualisation**: the data collection module writes a data file to disk, which is later used by the visualisation module. Importantly, these two phases do not need to be run on the same machine. The data files constitute the API between the two packages, and are kept general and well-specified. This allows data to be collected by one user, and sent off elsewhere for analysis by another user.

The workflow for using MARPLE is as follows:

 1. **Collect data** - specify areas of interest and duration of collection as [[#Collecting data | command line arguments], and MARPLE will collect data and write it to disk.

 2. *(optional)* **Transfer collected data to another machine** - the data can be moved to another machine and still viewed.

 3. **Display data** - specify the input data file, and MARPLE will automatically select the best visualiser to display this data. Alternatively, defaults can be set in the [configuration file](#configuration) or pass as [command line arguments](#displaying-data).

The [datatypes](#datatypes) that make up the data file written to disk are therefore the sole interface between the data collection and the data display modules.

<a name="marple_design"></a>
![The design structure of MARPLE](./res/design.svg)

**Figure:** The design structure of MARPLE. **TODO UPDATE THIS**

### The data collection package
Data collection occurs in two phases: first the data is collected, and then it is later written to disk. The user passes [command line arguments](#collecting-data) to specify which data should be collected, as well as the duration for which that data should be collected.

More specifically, data collection proceeds as follows:
 1. Argument parsing.
 2. Creation of a **Collecter** object and a **Writer** object.
 4. Invoking the **Collecter** to collect data, and passing this to the **Writer** to write it to disk.

This high-level procedure is carried out in the `collect.controller` package. The various classes used are detailed below:

**Collecter**

 * A base class implemented in `collect.interface.collecter`, from which all data collection classes derive.
 * Each type of data we wish to collect has a data collection class deriving from this base class.
 * Each data collection class therefore implements an **Options** class to encapsulate any options that may be passed (and a corresponding `_DEFAULT_OPTIONS` instance), an `__init__` method, and a `collect` method (which lazily returns the collected data). The `__init__` method takes as arguments the duration for which data should be collected, and an **Options** object.

**Writer**
 * A base class implemented in `collect.IO.write`, from which all file-writing classes derive.
 *  Implements a `write` method, which takes in a data generator, a filename, and a header. It then writes the data to the filename in a known format (see [[MARPLE#Datatypes|the section on datatypes]]).


#### Interfaces

There are a few different tools used to collect data, and the interfaces to these are detailed below.

##### Perf

Sometimes referred to as `perf-events`, `perf` is a Linux performance-analysis tool built into Linux from kernel version 2.6.31. It has many subcommands and can be difficult to use, but in MARPLE the perf workflow follows two phases:
 1. `$ perf record` - record performance data into a binary file (`perf.data`).
 2. `$ perf script` - decode the binary file to show the raw data.

The interface to this tool is in `collect.interface.perf`. It consists of several **Collecter**-derived classes, each of which encapsulate data collection on a different aspect of the system. Currently, MARPLE can collect data on the following aspects of the system using `perf`:
  * Memory: load and store events (with call graph information)
  * Memory: calls to malloc (with call graph information)
  * Stack: stack traces
  * CPU: scheduling events
  * Disk: block requests
 The module also contains a **StackParser** class, for converting call graph information from `perf` into [MARPLE standard datatypes](#datatypes).

 For more information on `perf`, see [Brendan Gregg's blog](http://www.brendangregg.com/perf.html).

##### Iosnoop

This is another Linux tool, designed for usage on Linux kernel versions 3.2 and later. It is part of Brendan Gregg's [perf-tools](https://github.com/brendangregg/perf-tools), which use [perf](#perf) and another Linux tool called `ftrace`. `Iosnoop` itself uses `ftrace`, and traces disk IO. It provides details of disk events such as the accessing command and its PID, the type of access, the starting block and number of bytes accessed, and the access latency. It can optionally provide the start and end times of the access.

MARPLE therefore uses `iosnoop` to trace disk latency, using a single **Collecter**-derived class. The `iosnoop` script resides in `util.perf-tools`, while the interface to it is in `collect.interface.iosnoop` - the interface calls the script using its timeout option to record data for a specific duration, and then parses the output and yields single [datapoints](#datatypes).

##### eBPF and BCC

[Berkeley Packet Filter](https://prototype-kernel.readthedocs.io/en/latest/bpf/ | Extended Berkeley Packet Filter) (eBPF) is derived from the [https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/Documentation/networking/filter.txt](Berkeley Packet Filter) (BPF, also known as Linux Socket Filtering or LSF). BPF allows a user-space program to filter any socket, blocking and allowing data based on any criteria. BPF programs are executed in-kernel by a sandboxed virtual machine. Linux makes this process relatively straightforward compared to other UNIX flavours such as BSD - the user simply has to write the code for the filter, then send it to the kernel using a specific function call.

eBPF has extended BPF to give a general in-kernel virtual machine, with hooks throughout the kernel allowing it to trace more than just packets, and do more actions than simple filtering. The user writes a program, which is compiled to BPF bytecode and sent to the kernel. The kernel then ensures that an eBPF program cannot harm the system, using static analysis before loading to ensure that it terminates and is safe to execute. It then uses BPF to execute the program, making use of kernel-/user-space probes for dynamic tracing (kprobes and uprobes respectively) and other tracepoints for static tracing and more (see [the eBPF workflow diagram](#ebpf_workflow)). The eBPF programs also use eBPF maps, a generic data structure for storing resulting information. A single eBPF program can be attached to many events, and many programs can use a single map (and vice-versa). Linux kernel versions 3.15 and onwards support eBPF.

<a name="ebpf_workflow"></a>
![eBPF workflow](http://www.brendangregg.com/eBPF/linux_ebpf_internals.png)

**Figure:** The worflow of using eBPF.

The [BPF Compiler Collection](https://github.com/iovisor/bcc) (BCC) is a "toolkit for creating efficient kernel tracing and manipulation programs", generally requiring Linux kernel version 4.1 or higher. BCC uses eBPF extensively, and makes it simpler to write eBPF programs by providing a Python interfaces to the various tools. The eBPF programs are written in C, and handled in strings in the BCC code. Many useful example tools are provided too (see [the diagram below](#bcc_tools)).

<a name="bcc-tools"></a>

![BCC tools](https://raw.githubusercontent.com/iovisor/bcc/master/images/bcc_tracing_tools_2017.png)

**Figure:** The BCC tools collection.

Currently, MARPLE uses the following BCC tools:
 * `mallocstacks` - traces `libc` `malloc()` function calls for memory allocation, and shows call stacks and the total number of bytes allocated. Interfaced by the **MallocStacks** class.
 * `memleak` - traces the top outstanding memory allocations, allowing for detection of memory leaks. Interfaced by the **MemLeak** class.
 * `tcptracer` - traces TCP `connect()`, `accept()`, and `close()` system call. In MARPLE this is used to monitor inter-process communication (IPC) which uses TCP. Interfaced by the **TCPTracer** class.

The BCC scripts can be found in `util.bcc-tools`, and their interface **Collecter**-derived classes are found in `collecter.interface.ebpf`.

For more information on these tools, see [Brendan Gregg's blog](http://www.brendangregg.com/ebpf.html).


##### Smem

The `smem` [memory reporting tool](https://www.selenic.com/smem/) allows the user to track physical memory usage, and takes into account shared memory pages (unlike many other tools). It requires a Linux kernel which provides the "Proportional Set Size" (PSS) metric for reporting a process' proportion of shared memory - this is usually version 2.6.27 or higher.

MARPLE uses `smem` to regularly sample memory usage, outputting data with times, PID/command name, and memory usage. The interface to `smem` is written in `collect.interface.smem`.

The tool has a very high latency - it was initially used as it helpfully sorts the processes recorded by memory usage. This is not strictly necessary however, so a command such as `top` could be used in its place. Alternatively, the `smemcap` is a lightweight version designed to run on resource-constrained systems - see the bottom of [the man page](https://linux.die.net/man/8/smem). Tests also need to be written for this MARPLE module. **TODO**

### The data display package
Data display proceeds as follows:

 1. Argument parsing.
 2. Creation of a **GenericDisplay** object.
 3. Calling the `show()` method of the **GenericDisplay**, which will save and display the data visualisation.

This high-level procedure is carried out in the `display.controller` package. The **GenericDisplay** class is are detailed below:

**GenericDisplay**
 * A base class implemented in `display.controller.generic_display`, from which all data display classes derive.
 * Each data visualiser used by MARPLE has a data display tool deriving from this base class.
 * Each data display class therefore implements a a `show(self)` method, which will show and save the visualisation.

There are a few different tools used to display data, and these are detailed below.

#### Flamegraphs
[Brendan Gregg's flame graphs](http://www.brendangregg.com/flamegraphs.html) are a useful visualisation for profiled software, as they show call stack data. They are very simply generated using the [open-source tool](https://github.com/brendangregg/FlameGraph), a copy of which can be found in `util.flamegraph`. The interface to this tool is located in `display.flamegraph`. The interface reads from a standard MARPLE data file to produce standard MARPLE stack data (see [the section on datatypes](#datatypes)). It then uses the Python `collections` library to calculate a weighted count of the occurrences of each stack, outputting them to a temporary file in a format readable by the flame graph Perl script. The `show()` method then invokes this script to save and display the file using Mozilla Firefox. An example taken from Brendan Gregg's website is [below](#flame_graph). Flame graphs are interactive, allowing the user to zoom in to a certain process.

<a name="flame_graph"></a>
![flamegraph](./res/flamegraph.svg)

**Figure:** An example flame graph, showing CPU usage for a MySQL program.

MARPLE uses flame graphs for many visualisation, and in general any form of stack data is easily viewed as a flame graph.

#### Tree maps

[Tree maps](http://d3plus.org/examples/advanced/9860411/), like [flamegraphs](#flamegraph), are a useful visualisation tool for call stack data. Unlike flame graphs, which show all levels of the current call stack at any one time, tree maps display only a single level, giving users a more detailed view of that level and the opportunity to drill down into deeper levels. Just as with flame graphs, these are easily generated using an external library - [D3 plus](https://d3plus.org/). D3 plus is a JavaScript library which extends the popular [D3.js](https://d3js.org/). MARPLE uses a Python interface to D3 plus known as [D3IpyPlus](https://github.com/maclandrol/d3IpyPlus) - this can be found in `util.d3IpyPlus`. D3IpyPlus attempts to incorporate D3 plus into the [IPython Notebook](https://ipython.org/notebook.html) computational environment (soon to be renamed Jupyter Notebook).

The tree map class in MARPLE is located in `display.treemap`, and first reads data from a standard MARPLE data file into a standard MARPLE datatype. It then converts this data into a format readable by the D3IpyPlus libraries, and writes this to file. Lastly, it uses the library to display the data, as shown in [the figure below](example_treemap). These tree maps are interactive, allowing the user to see useful information on hover, and drill down into each node of the tree.

<a name="example_treemap"></a>
[Example treemap](./res/treemap.html)

**Figure:** An example tree map, showing stack trace data. **TODO figure out how to embed this**

#### Heat maps

Heat maps allow three-dimensional data to be visualised, using colour as a third dimension. In MARPLE, heat maps are used as histograms - data is grouped into buckets, and colour is used to represent the amount of data falling in each bucket. It is generally expected that heat maps in MARPLE will have an x-axis representing time.

MARPLE uses the [NumPy](http://www.numpy.org/) and [Matplotlib](https://matplotlib.org/) Python libraries to create and display heat maps. The heat map module is in `display.heatmap`, and it defines the following classes:

**AxesLabels**
 * A class deriving from **typing.NamedTuple**, which allows the display controller to pass in labels for the heat map axes and colorbar.

**GraphParameters**
 * A class deriving from **typing.NamedTuple**, allowing the display controller to pass in varying graph parameters such as the size of the generated figure, the scale of the graph (i.e. the density of bins), and the resolution of the y-axis (i.e. how dense bins are on the y-axis).

**HeatmapException**
 * An exception thrown by the **HeatMap** class on encountering an error.

**HeatMap**
 * A class encapsulating the heat map itself, deriving from **GenericDisplay** (see [above](#the-data-display-package)).
 * The `__init__` method takes as arguments the input data filename, the desired output image filename, an **AxesLabels** object for labelling of axes, a **GraphParameters** object of graph setup, and a boolean which is true if the x-axis should be normalised. Setting this latter boolean means that the x-axis data will be normalised to start from zero, with the intention of representing time from the start of data collection.
 * As with all **GenericDisplay**-derived classes, **HeatMap** implements a `show()` method to save and display the heat map.
 * The **HeatMap** constructor first extracts the data from the file, then calculates some basic statistics from the data. It then creates the axes using Matplotlib, and uses !NumPy to create a histogram array. It uses the data statistics to set the viewport on the heat map. A colorbar is also added. Using the `show()` method to display the heat map gives an interactive Python window containing the figure.

 The resulting heat map is interactive: the user can hover over the figure to show annotations about the data currently under the cursor. The axes are scrollable using the two bars on top of the heat map (see [the figure below](#example_heatmap )). The **HeatMap** class attempts to automatically choose an appropriate viewport and zoom level based on the input **GraphParameters** object. In general, it tries to ensure that at least a certain number of histogram bins (passed within the **GraphParameters** object are visible below the median y-axis value (this does not work well for very negatively-skewed data).

<a name="example_heatmap"></a>
![heatmap](./res/heatmap.png)

**Figure:** An example heat map, showing disk latency data.

#### G2

[G2](https://wiki.fd.io/view/VPP/g2) is an event-log viewer. It is very efficient and scalable, and is part of the [Vector Packet Processing](https://wiki.fd.io/view/VPP) (VPP) platform. This is a framework providing switch/router functionality, and is the open-source version of Cisco's VPP technology. The [VPP Git repository](https://gerrit.fd.io/r/vpp) is therefore included in MARPLE using the [Git submodule feature](https://git-scm.com/docs/gitsubmodules).

When used in MARPLE, G2 reads data to display from a binary file format called CPEL. CPEL is an ELF-like format for events, and the documentation can be found [here](https://wiki.fd.io/view/VPP/cpel). NB: CPEL files store event times using two 32-bit unsigned longs, which give time in units of CPU ticks when concatenated. If instead time is stored in units of microseconds, setting the number of ticks per microsecond to 1,000,000 results in a correct timescale.

See [below](#g2_example) for an example G2 window.

<a name="g2_example"></a>
![g2](./res/g2.png)

**Figure:** An example G2 window, showing scheduling event data.

G2 has many display features, a few of these are listed below.
 * Pressing the 'c' key will colour the graph.
 * Multiple 'tracks' of events are displayed, and their labels are shown on the left. In the figure above, the tracks are CPU cores.
 * The events are ordered chronologically, with a timescale at the bottom of the screen.
 * Event types can be hidden/shown using the checkboxes on the right.
 * There are navigational and search controls along the bottom of the screen, and in the lower-right conrner.

 For more information, consult the [G2 wiki](https://wiki.fd.io/view/VPP/g2).

#### Stack plots

Stack plots (also known as stacked graphs or stacked charts) show 'parts to the whole'. They are effectively line graphs subdivided to show the various components that make up the overall line value. They can be seen as a form of pie chart, but one that changes with respect to another dimension (usually time). An example stack plot is shown [below](#stackplot_example).

<a name="stackplot_example"></a>
![stackplot](./res/stackplot.png)

**Figure:** An example stack plot, showing memory usage by process over time.

The **GenericDisplay**-derived class (see [above](#the-data-display-package)) that handles stack plot functionality can be found in `display.stackplot`, and is called **StackPlot**. It makes use of the [Matplotlib stackplot](https://matplotlib.org/gallery/lines_bars_and_markers/stackplot_demo.html) feature for easy generation of the plot.

The constructor reads data points from a [standard MARPLE data file](#datatypes), then aggregates data points which coincide at the same x-axis value for each possible x-axis value. It selects the largest contributing y-axis values amongst these (along with their labels) - the number selected depends on the parameter input to the constructor. The rest of the datapoints are conglomerated into an 'other' category so that the display does not become cluttered with many small contributions.

These are then sorted into display order. The Matplotlib stack plot functionality plots data in the order it receives it - the first item is receives is the lowermost contribution on the stack plot. However the labels in the plot legend are the other way around ([example](https://matplotlib.org/_images/sphx_glr_stackplot_demo_001.png)) so these must be reversed.

Importantly, each x-axis value must have the same number of y-axis categories (i.e. the same number of stacked contributions). The **StackPlot** class has functionality to do this before the data is displayed in the `show()` function.

**TODO:** This module needs work:
 * There are many @@@s in the comments.
 * Unit tests must be written.
 * File handling must be brought more in line with the rest of the display modules - using standard datatypes etc.
 * Code review for readability.

## Common modules
There are a number of modules in common to both the data collection and the data display modules. Their functionality is outlined below.

### Datatypes
MARPLE defines some standardised datatypes, and standard ways of writing these to files. These datatypes effectively form the interface between the data collection and the data display modules, and are kept as general as possible so that they can be used for multiple collection/display modes. All derive from **typing.NamedTuple**, and are defined in `common.datatypes`. Each datatype implements a `__str__` and a `from_string` method, defining their standard conversions to and from strings respectively. The various datatypes are summarised below.

**Datapoint data**
 * The standard string representation for a **Datapoint** object is "`x`,`y`,`info`".

**Event data**
 * The **EventData** class represents events. An **EventData** object has a `time` field for the time of the event, a `type` field for the type of event, and a `datum` field for any other accompanying data.
 * The standard string representation for an **EventData** object is "`time`,`track`,`datum`".

**Stack data**
 * The **StackData** class represents stacks. A **StackData** object has a `weight` field for the weight of the stack (how significant it is), and a `stack` tuple for the stack itself.
 * The standard string representation for a **StackData** object is "`weight`#`stack1`;`stack2`;...".

A standard MARPLE data file is a plain text file, with a header and data. The header is the first line (see [below](#headers) for more information on headers), and every other line in the file is the standard string representation of a MARPLE standard datatype.

#### Headers

A MARPLE header is a JSON string - each MARPLE data file has a header. It will usually contain the following keys:

`start`
 * The time at which the data started being collected.

`end`
 * The time at which data stopped being collected.

`interface`
 * What data was collected - this will directly correspond to a single one of the **Collecter**-derived classes (see [above](#the-data-collection-package)).

`datatype`
 * The type of data that was collected - this will directly correspond to a single one of the standard datatypes described [above](#datatypes).

### File-handling
MARPLE must write several types of files to disk in general operation. The functionality for file naming conventions is in `common.file`, and consists of the following classes:

**_FileName**
 * The base class for all file names used in MARPLE.
 * The constructor takes in `option`, `extension`, `given_name`, and `path`. It determines the current datetime and saves that in an object field. By default, `given_name` is `None` and `path` is the output directory (`OUT_DIR`) defined in `common.paths`.

 **DisplayFileName**
  * Derives from **_Filename**, and is intended for display output files.
  * By default, its `extension` is "`marple.display`", and it has no `option`.
  * Implements a `set_options` method, to allow display modules to change the `option` and `extension` fields to suit their output. The intention is that the `option` field is set to the type of visualisation (tree map, heat map, and so on) and the extension is set as necessary for the visualisation (`.svg`, `.html`, and so on).

 **DataFileName**
 * Derives from **_Filename**, and is intended for data output files.
 * Extensions are `.marple` unless a `given_name` is specified.
 * Implements an `export_filename` method, which writes the file name (obtained from `__str__`) to the variable directory (`VAR_DIR` from the `common.paths` module) in a file named `filename`.
 * Implements an `import_filename` method, which reads a file name from the variable directory file described above.
 * The intention of these two methods is to allow the user to display the most recently recorded data without having to pass command line arguments. This is for the usage pattern of recording and immediately displaying data on the same machine. The data file name for the recorded is saved using `export_filename` in the data collection module, then read using `import_filename` in the data display module.

 **TempFileName**
 * Derives from **_Filename**, and is intended for temporary files.
 * There is no `option`, the `extension` is set to "`tmp`", and the `path` is set to the temporary directory (`TMP_DIR` in `common.paths`).

### Util
Some utilities are defined in `common.util`. These are as follows:
 * `check_kernel_version` - a decorator that allows MARPLE functions to check the Linux kernel version before execution, to ensure that a high enough version is used.
 * `Override` - a decorator that indicates a function overrides one in a superclass. The superclass is passed as an argument. This is an imitation of the [Java annotation](https://docs.oracle.com/javase/8/docs/api/java/lang/Override.html ) (`@Override`).
 * `log` - a decorator that takes in a logging object. When applied to a function, it logs entry and exit of the function, as well as any passed arguments. If an exception is raised, this too is logged.

### Configuration, Exceptions, Output, and Paths
 * MARPLE uses a `config.txt` file in the top-level directory to specify its configuration. This is parsed using a Python `configparser` object, and the functionality is in `common.config`.
 * The necessary directory paths used in MARPLE are specified in `common.paths`.
 * Some exceptions used in MARPLE are specified in `common.exceptions`.
 * Some methods of user output (which print to `stdout` or `stderr` and the MARPLE log simultaneously) are found in `common.output`.

## Testing
Due to the short nature of the project, rigorous testing was not a main focus of MARPLE. However wherever possible, unit tests were written for each module, using the Python `unittest` framework. No component or integration tests were written.

The [pytest](https://docs.pytest.org/en/latest/) framework was used to run tests - it automatically finds tests recursively in the current directory, and runs them. This was used with the [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) plugin, which tracks code coverage as a proportion of lines of code for this project.

### Travis CI
Testing was automated using the popular [Travis CI](https://travis-ci.org/ensoft/marple), a continuous integration platform. The key idea behind [continuous integration](https://en.wikipedia.org/wiki/Continuous_integration) (CI) is to avoid integration problems ("integration hell") by integrating early and frequently wherever possible. Rather than working on branches for extended periods of time (which become outdated as other developers make changes to the mainline branch) and spending excessive time integrating changes to account for this, under CI developers will make changes to the mainline branch early and often. It is therefore good practice to have a suite of unit tests for developers to run before submitting changes, with integration tests run automatically on a CI server.

However, for this project there are no integration tests. Travis CI therefore first installs the necessary prerequisites for MARPLE (other than G2 currently - see [here](#g2), and runs all unit tests (measuring code coverage too) on any push to the `master` branch of the MARPLE !GitHub repository. It also runs [Pylint](https://www.pylint.org/) on the project to check for errors. If either of these two result in any errors (i.e. a non-zero exit code), the CI build fails.

Once the unit tests and Pylint have passed, Travis CI collects further information. It runs Pylint again, checking for warnings too and computing a Pylint score - this score is then used to generate a badge using [anybadge](https://github.com/jongracecox/anybadge). Pylint is run with the Ensoft configuration file, which can be found on the [MARPLE GitHub repository](https://github.com/ensoft/marple/blob/master/pylintrc.txt).

The code coverage report is then exported to [Codecov](https://codecov.io/github/ensoft/marple). Codecov is a platform giving visualisations of code coverage, and storing reports.

The unit tests, code coverage tests, and Pylint tests each produce output which is collected and sent to [Amazon S3](#amazon-s3). Badges for each can be found at the top of this document.

For more details on the MARPLE Travis CI build, see the [.travis.yml](https://github.com/ensoft/marple/blob/master/.travis.yml) file on the MARPLE GitHub repository.

#### Amazon S3

[Amazon S3](https://aws.amazon.com/s3/) offers widely-used cloud storage, with well-documented usage. In particular, Travis CI has the ability to [upload test artifacts to Amazon S3 servers](https://docs.travis-ci.com/user/uploading-artifacts/). This allows the unit test, code coverage, and Pylint reports to be uploaded to cloud storage. In addition, the Pylint badge is uploaded to the servers too.

The Amazon S3 bucket used with MARPLE is in the `us-west-1` region (US West, N. California) and is named [marple.ci.logs](https://s3-us-west-1.amazonaws.com/marple.ci.logs). The Amazon S3 account is registered to hrutvik.kanabar@ensoft.co.uk, and uses the free 12-month trial period (starting on 13/08/2018, and expiring on 12/08/2019).

## Future tasks
### Demo with Simon on 10/08/18
 * Gather all data at once - ideally into one output file.
 * Create a web interaction for display module UI - for displaying multiple data sources at once.
  * Could initially be basic, open all images produced in separate tabs.
  * Later, a proper interactive UI.
 * Create a memory-mapping tool to show which parts of installed RAM are being used and for what.

### Meeting on 02/08/18
 * Create an interface to the interfaces - allow it to choose which to use based on passed arguments and config file.
 * Add further arguments to UI to allow for different types of data collection.
   * Consider possibility of collecting multiple types at once (e.g. 'collect --disk --latency,block_requests' or similar).
 * Add changes to XML module layout file.

### Backlog
 * Discuss and decide our general approach to exception handling - refactor code to match.
 * Move unit tests to a separate test directory (i.e. not within collect/display)?
 * Split `util` to put collect/display-specific stuff into collect/display respectively?
   * Also rename `util` to something more informative.

## References
### General Profiling
 * [Linux tracing systems ](https://jvns.ca/blog/2017/07/05/linux-tracing-systems/ )
 * [Brendan Gregg's website ](http://www.brendangregg.com/ )

### Memory
 * [glibc malloc](https://sploitfun.wordpress.com/2015/02/10/understanding-glibc-malloc/ )
 * [Syscalls used by malloc](https://sploitfun.wordpress.com/2015/02/11/syscalls-used-by-malloc/ )
