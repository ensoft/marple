# MARPLE - Multi-tool Analysis of Runtime Performance on Linux Environments


## Description
MARPLE is a tool designed to provide an easy way to collect and display Linux performance data such as CPU events, memory allocations, efficiency of IPC, etc.<BR>

There is a wide variety of Linux tools for this purpose, such as perf, ftrace, strace, eBPF, ... which are very powerful but need some time to grasp and get comfortable using.<BR>

MARPLE provides an interface to these these tools that is quick and easy to use as a first step in analysing the system. <BR>It also has facilities to display the data graphically to help visualise problems which is useful for both software engineers and system analysts.

## Design
The design is modular, with a controller module as the user interface at the top, different function modules in the middle, <BR>and lower level modues interaction directly with the system, other tools and the file system. <BR>The controller is the point of contact through which the user can interact with lower level system tools. <BR>The main focus is transparency, i.e. the user just specifies what part of the system she wants to analyse <BR>and the tool infers what lower level module is most suitable for the task, <BR>be it using trace points or k-probes, without the user having to worry about these details.

![design](./res/design.svg)

<BR>

**Figure 1:** Modular structure of the MARPLE tool with three layers of modules.

## Setup and execution (preliminary)
  make sure you have python 3 and perl installed

 1. clone or download the git repository at [https://github.com/ensoft/marple](https://github.com/ensoft/MARPLE)

 2. install linux-tools (needed for perf to work)

~~~~

sudo apt-get install linux-tools-generic linux-tools-common linux-tools-`uname -r`

~~~~

  change the sudoers file to adopt changes to PYTHONPATH:

~~~~

sudo visudo

#add the following line:

Defaults        env_keep += "PYTHONPATH"

#exit and save

^X

~~~~

  The following currently needs to be run every time a new shell session is started:

~~~~

#cd to the code directory, e.g.:

cd ~/PycharmProjects/marple

#export python environment variable

export PYTHONPATH=.

#create an alias to smoothly call the command (preliminary solution)

alias marple='sudo python3 main.py'

~~~~

  Now, marple commands can be executed as described in the "API" section, e.g.:

~~~~

marple collect -s -f "outputfile" -t 5

~~~~

Note: In order to run the display module, you currently need to change the method in the display/flamegraph.py module to change user to your username.

## API
The program can be called with two main functions: one for collecting data and one for displaying it.<BR>

Note here we assume the program has been built into an executable.

### Collecting data
~~~~

usage: marple collect [-h] (-s | -l | -i | -m) [-f FILE] [-t TIME]

optional arguments:

  -h, --help            show this help message and exit

  -c, --cpu             cpu scheduling data

  -i, --ipc             ipc efficiency

  -l, --lib             library load times

  -m, --mem             memory allocation/ deallocation

  -s, --stack           stack tracing

  -f FILE, --file FILE  Output file where collected data is stored

  -t TIME, --time TIME  time in seconds that data is collected

~~~~

### Displaying data
~~~~

optional arguments:

  -h, --help            show this help message and exit

  -c, --cpu             cpu scheduling data

  -i, --ipc             ipc efficiency

  -l, --lib             library load times

  -m, --mem             memory allocation/ deallocation

  -s, --stack           stack tracing

  -g                    graphical representation as an image (default)

  -n                    numerical representation as a table

  -f FILE, --file FILE  Input file where collected data to display is stored

~~~~

## Flamegraphs
One of the options for displaying collected data is Brendan Gregg's [Flamegraph](http://www.brendangregg.com/flamegraphs.html ) tool.<BR>

Here is an example of what it looks like (click to expand tasks): <BR>

<BR>

![flame](./res/flame.svg)

<BR>

**Figure 2:** An interactive example of a visualization of scheduling data as a flamegraph.

## g2
### Installation instructions by the creator himself (Dave Barach)
~~~~

# Make sure you have the “libgtk2.0-dev” package installed.

apt install libgtk2.0-dev

# Clone repository

$ git clone https://gerrit.fd.io/r/vpp

# Configure

$ cd src

$ libtoolize

$ aclocal

$ autoconf

$ automake --add-missing

$ autoreconf

# Go to build directory and install

$ cd ../build-root

$ make g2-install

~~~~

### How to use
~~~~

# Run

$ ./install-native/g2/bin/g2

# usage:

g2 [--pointdefs <filename>] [--event-log <filename>]

   [--ticks-per-us <value>]

   [--cpel-input <filename>] [--clib-input <filename]>

G2 (x86_64 GNU/Linux) major version 3.0

Changed Thu Dec 14 17:18:36 EST 2017

~~~~

### How to convert to cpel
~~~~

$ make perftool-install

<snip>

$ ls install-native/perftool/bin/

c2cpel      cpeldump   cpelstate  elog_merge

cpelatency  cpelinreg  elftool   

 

~~~~

## Future tasks
 * g2 representation for scheduler, ipc?

 * flamegraph for memory

 * use configparser for configuration file

 * make a function that defines default values: first user input, then default file, then local constants

 * pipe the errors of subprocess.Popen calls (asynchronously?) to the log

 * wait on subprocesses or not? Should be yes.

## References
The following is a list of resources for system profiling.

### General Profiling
 * [Linux tracing systems ](https://jvns.ca/blog/2017/07/05/linux-tracing-systems/ )

 * [Choosing a linux tracer](http://www.brendangregg.com/blog/2015-07-08/choosing-a-linux-tracer.html )

 * [Linux tracing in 15 minutes](http://www.brendangregg.com/blog/2016-12-27/linux-tracing-in-15-minutes.html )

 * [USE methodology](http://www.brendangregg.com/usemethod.html )

 * [USE methodology - Linux checklist](http://www.brendangregg.com/USEmethod/use-linux.html )

 * [perf](http://www.brendangregg.com/perf.html )

 * [eBPF](http://www.brendangregg.com/ebpf.html )

### CPU/Scheduler
### Memory
 * [glibc malloc](https://sploitfun.wordpress.com/2015/02/10/understanding-glibc-malloc/ )

 * [Syscalls used by malloc](https://sploitfun.wordpress.com/2015/02/11/syscalls-used-by-malloc/ )

 * [Memory flamegraphs](http://www.brendangregg.com/FlameGraphs/memoryflamegraphs.html )

### DLLs
### IPC
 * [TCP tracepoints](http://www.brendangregg.com/blog/2018-03-22/tcp-tracepoints.html )

 * ['tcplife' - uses BCC](http://www.brendangregg.com/blog/2016-11-30/linux-bcc-tcplife.html )

 * ['tcptop' - uses BCC](http://www.brendangregg.com/blog/2016-10-15/linux-bcc-tcptop.html )

 * [more TCP & BCC usage](http://www.brendangregg.com/blog/2015-10-31/tcpconnect-tcpaccept-bcc.html )

 * [TCP retransmit - uses ftrace](http://www.brendangregg.com/blog/2014-09-06/linux-ftrace-tcp-retransmit-tracing.html )

### Visualisation
 * [g2 event log viewer](https://wiki.fd.io/view/VPP/g2 )

 * [repository including g2 tool](https://gerrit.fd.io/r/vpp )

 * [Flamegraphs](http://www.brendangregg.com/flamegraphs.html )

 * [Flamegraphs github](https://github.com/brendangregg/FlameGraph )

