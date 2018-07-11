# -------------------------------------------------------------
# perf_to_stacks.py - converts formatted perf output to stack lists
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Converts formatted perf output to stack lists

This module is a Python adaptation of Brendan Gregg's Perl script
stackcollapse-perf.pl from his flamegraph repository.
It differs in that it has fewer options and returns a generator to get
single stacks lazily and without counting them.
This is in order to integrate it with the marple program structure.

"""

import sys
import re
import logging

INCLUDE_TID = False
INCLUDE_PID = False

logger = logging.getLogger('stack_to_lines')
logger.setLevel(logging.DEBUG)


def parse(input_):
    """
    Goes through input line by line to fold the stacks

    :param input_:
        A text file or similar input containing lines of stack data
        output from perf.

    :return:
        A generator of lists that contain information about a single stack.
    """
    global pid, comm
    stack = []
    pname = None
    event_filter = ""
    event_defaulted = False
    event_warning = False

    for line in input_:
        # If end of stack, save cached data.
        if re.match("^$", line) is not None:
            # ignore filtered samples
            if pname is None:
                continue
            stack.insert(0, pname)
            if stack:
                yield stack
            stack = []
            pname = None
            continue

        #
        # event record start
        #
        if re.match("(\S.+?)\s+(\d+)/*(\d+)*\s+", line) is not None:
            # Matches "perf script" output, first line of a stack (baseline)
            # eg, "java 25607 4794564.109216: cycles:"
            # eg, "java 12688 [002] 6544038.708352: cpu-clock:"
            # eg, "V8 WorkerThread 25607 4794564.109216: cycles:"
            # eg, "java 24636/25607 [000] 4794564.109216: cycles:"
            # eg, "java 12688/12764 6544038.708352: cpu-clock:"
            # eg, "V8 WorkerThread 24636/25607 [000] 94564.109216: cycles:"
            # other combinations possible
            m = re.match("(\S.+?)\s+(\d+)/*(\d+)*\s+", line)
            try:
                (comm, pid, tid) = m.group(1), m.group(2), m.group(3)
            except IndexError:
                # No tid found
                tid = pid
                pid = "?"
            m = re.search("(\S+)", line)
            if m is not None:
                # By default only show events of the first encountered
                # event type. Merging together different types, such as
                # instructions and cycles, produces misleading results.
                event = m.group(1)
                if event_filter == "":
                    # By default only show events of the first
                    # encountered event type. Merging together different
                    # types, such as instructions and cycles, produces
                    # misleading results.
                    event_filter = event
                    event_defaulted = True
                elif event != event_filter:
                    if event_defaulted and not event_warning:
                        # only print this warning if necessary:
                        # when we defaulted and there was
                        # multiple event types.
                        logger.error("Filtering for events of type {}"
                                     .format(event_filter))
                        event_warning = True
                    continue

            (m_pid, m_tid) = pid, tid

            if INCLUDE_TID:
                pname = "{}-{}/{}".format(comm, m_pid, m_tid)
            elif INCLUDE_PID:
                pname = "{}-{}".format(comm, m_pid)
            else:
                pname = comm

            # original perl script has transliteration here: $pname =~ tr/ /_/;

        #
        # stack line
        #
        elif re.match("\s*(\w+)\s*(.+)\((\S*)\)", line) is not None:
            # Matches the other lines of a stack, i.e. the ones above the base.
            # e.g ffffffffabe0c31d _intel_pmu_enable_ ([kernel.kallsyms])
            m = re.match("\s*(\w+)\s*(.+)\((\S*)\)", line)

            # ignore filtered samples
            if pname is None:
                continue

            pc, rawfunc, mod = m.group(1), m.group(2), m.group(3)

            # Linux 4.8 included symbol offsets in perf script output by
            # default, eg:
            # 7fffb84c9afc cpu_startup_entry+0x800047c022ec ([kernel.kallsyms])
            # strip these off:
            re.sub("\+0x[\da-f]+$", "", rawfunc)

            # Original perl script adds inline here if required by user

            # skip process names
            if re.match("\(", rawfunc):
                continue

            inline = []
            for func in re.split("->", rawfunc):
                if func == "[unknown]":
                    # use module name instead, if known
                    if mod != "[unknown]":
                        func = mod
                        re.sub(".*/", "", func)

                    # Original perl script has option to include address.
                # Original perl script has some optional tidying up here for
                # Java and other generic stuff

                if len(inline) > 0:
                    # Mark as inlined
                    func += "_[i]"

                inline.append(func)

            stack.insert(0, inline)

        else:
            logger.error("Unrecognized line: {}".format(line))


def main(argv):
    """Main converter function

    Goes through input line by line and creates stack objects, then prints them
    to stdout.

    """
    try:
        logger.info("Starting to convert perf output to stacks")
        with open(argv[1]) as f:
            gen = parse(f)
            for i in gen:
                print(str(i))
    except Exception as exc:
        print(exc)


if __name__ == "__main__":
    main(argv=sys.argv)
