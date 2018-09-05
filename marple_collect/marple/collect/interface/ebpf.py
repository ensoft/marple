# -------------------------------------------------------------
# ebpf.py - interacts with the eBPF tracing tool
# June - August 2018 - Franz Nowak, Andrei Diaconu
# -------------------------------------------------------------

"""
Interacts with the eBPF tracing tool

"""

__all__ = (
    "MallocStacks",
    "Memleak",
    "TCPTracer"
)

import asyncio
import datetime
import logging
import os
import re
import signal
import typing
from io import StringIO

from marple.collect.interface import collecter
from marple.common import util, data_io, paths, output
from marple.common.consts import InterfaceTypes

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)

BCC_TOOLS_PATH = paths.MARPLE_DIR + "/collect/tools/bcc-tools/"


class MallocStacks(collecter.Collecter):
    """
    Class that interacts with Brendan Gregg's mallocstacks tools

    """

    class Options(typing.NamedTuple):
        """ No options for this collecter class. """
        pass

    _DEFAULT_OPTIONS = None

    def __init__(self, time, options=_DEFAULT_OPTIONS):
        """
        Initialize the collecter

        """
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def _get_raw_data(self):
        """ Collect raw data asynchronously using mallocstacks. """
        self.start_time = datetime.datetime.now()

        sub_process = await asyncio.create_subprocess_exec(
            'sudo', 'python', BCC_TOOLS_PATH + 'mallocstacks.py', '-f',
            str(self.time),
            stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )
        out, err = await sub_process.communicate()

        self.end_time = datetime.datetime.now()
        self.log_error(err, logger)

        return StringIO(out.decode())

    @util.log(logger)
    @util.Override(collecter.Collecter)
    def _get_generator(self, raw_data):
        """ Convert raw data to standard datatypes and yield it. """
        for line in raw_data:
            yield data_io.StackDatum.from_string(line)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def collect(self):
        """ Collect data asynchronously using iosnoop."""
        raw_data = await self._get_raw_data()
        data = self._get_generator(raw_data)
        return data_io.StackData(data, self.start_time, self.end_time,
                                 InterfaceTypes.MALLOCSTACKS, "kilobytes")


class Memleak(collecter.Collecter):
    """
    Class that interacts with the memleak tool.

    Collects all the top 'top_stacks' stacks with outstanding allocations
    The memleak.py script places an ebpf program in kernel memory that
    places uprobes in all the userspace allocation and deallocation
    functions in the kernel. This program keeps track, using hashtables,
    of every stack's current allocated memory. If, by the end of a sleep
    period of 'time' seconds, there are stacks that haven't freed all the
    memory, the script prints them in a StackLine format
    (weight#name1;name2;name3;...).
    This class retrieves and processes this output.

    """

    class Options(typing.NamedTuple):
        """
        Options to use in the collection.
            - top_stacks: how many stacks to be displayed

        """
        top_stacks: int

    _DEFAULT_OPTIONS = Options(top_stacks=10)

    def __init__(self, time, options=_DEFAULT_OPTIONS):
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def _get_raw_data(self):
        """ Get raw data asynchronously using memleak.py """
        self.start_time = datetime.datetime.now()

        sub_process = await asyncio.create_subprocess_exec(
            'sudo', 'python', BCC_TOOLS_PATH + 'memleak.py',
            '-t', str(self.time), '-T', str(self.options.top_stacks),
            stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )

        out, err = await sub_process.communicate()
        self.end_time = datetime.datetime.now()
        self.log_error(err, logger)

        return StringIO(out.decode())

    @util.log(logger)
    @util.Override(collecter.Collecter)
    def _get_generator(self, raw_data):
        """ Convert raw data to standard datatypes and yield it """
        for line in raw_data:
            yield data_io.StackDatum.from_string(line)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def collect(self):
        """ Collect data asynchronously using memleak.py """
        raw_data = await self._get_raw_data()
        data = self._get_generator(raw_data)
        return data_io.StackData(data, self.start_time, self.end_time,
                                 InterfaceTypes.MEMLEAK, "kilobytes")


class TCPTracer(collecter.Collecter):
    """
    Trace local TCP system calls to connect(), accept(), and close().

    Uses the tcptracer script from BCC.
    Intended to trace IPC, so ignore all calls that involve non-local
    addresses (i.e. ones that do not start with '127.').
    Can be set to monitor only a single net namespace using the Options class.
    Collects data, then traverses it once to build up a dictionary mapping
    ports to PIDs/comms, then traverses again to yield event data.

    """
    class Options(typing.NamedTuple):
        """
        Options to use in the collection.

        .. attribute:: net_ns:
            The net namespace for which to collect data - all others will be
            filtered out.

        """
        net_ns: int

    _DEFAULT_OPTIONS = None

    def __init__(self, time, options=_DEFAULT_OPTIONS):
        """
        :param options:
            If options is None, then all namepsaces will be considered.

        """
        super().__init__(time, options)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def _get_raw_data(self):
        """
        Collect raw data asynchronously using tcptracer.

        Call tcptracer, and discard the KeyboardInterrupt error message
        resulting from terminating the script.

        """
        cmd = BCC_TOOLS_PATH + 'tcptracer ' + '-tv'

        self.start_time = datetime.datetime.now()
        sub_process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, preexec_fn=os.setsid
        )

        # Timeout the subprocess
        _, pending = await asyncio.wait(
            [asyncio.ensure_future(sub_process.communicate())],
            timeout=self.time
        )
        self.end_time = datetime.datetime.now()
        os.killpg(sub_process.pid, signal.SIGINT)

        out, err = await (pending.pop())

        # Check for unexpected errors
        # We expect tcptracer to print a stack trace on termination -
        # anything more than that must be logged
        pattern = r"^Traceback \(most recent call last\):" \
                  r"(\S*\s)*KeyboardInterrupt\s$"
        if not re.fullmatch(pattern, err.decode()):
            self.log_error(err, logger)

        return StringIO(out.decode())

    @util.log(logger)
    @util.Override(collecter.Collecter)
    def _get_generator(self, raw_data):
        """
        Convert raw data to standard datatypes and yield it.

        Traverse the data once to build up a dictionary mapping ports to
        PIDs/comms.
        Traverse the data again using that dictionary to output events with
        well-resolved PIDs/comms for ports (hopefully).
        Print and log error messages when ports cannot be resolved.

        :return:
            A generator of :class:`EventDatum` objects.

        """

        port_lookup_dict = self._generate_dict(raw_data)
        return self._generate_events(raw_data, port_lookup_dict)

    @util.log(logger)
    @util.Override(collecter.Collecter)
    async def collect(self):
        """ Collect data asynchronously using tcptracer """
        raw_data = await self._get_raw_data()
        data = self._get_generator(raw_data)
        return data_io.EventData(data, self.start_time, self.end_time,
                                 InterfaceTypes.TCPTRACE)

    @util.log(logger)
    def _generate_dict(self, data):
        """
        Generate a dictionary mapping ports to sets of (PID, comm) pairs.

        :param data:
            The input tcptracer data
        :return:
            The port-mapping dictionary.

        """
        # Skip two lines of header
        data.seek(0)
        data.readline()
        data.readline()

        # Use a Python dictionary to match up ports and PIDS/command names
        port_lookup = {}

        # Process rest of file
        for line in data:
            values = line.strip().split()
            pid = int(values[2])
            comm = values[3]
            source_addr = values[5]
            dest_addr = values[6]
            source_port = int(values[7])
            net_ns = int(values[9])

            # Discard external TCP / not in net namespace
            if not source_addr.startswith("127."):
                continue
            elif not dest_addr.startswith("127."):
                continue
            elif self.options and self.options.net_ns != net_ns:
                continue

            # Add the port data to port_lookup dictionary
            if source_port in port_lookup:
                # Already in dictionary, union sets
                port_lookup[source_port] = \
                    {(pid, comm)}.union(port_lookup[source_port])
            else:
                port_lookup[source_port] = {(pid, comm)}

        return port_lookup

    @util.log(logger)
    def _generate_events(self, data, port_lookup):
        """
        Generate EventDatum objects using tcptracer data and the port-mapping
        generated from that data by _generate_dict

        :param data:
            The tcptracer data.
        :param port_lookup:
            The port-mapping dictionary generated from that data by
            _generate_dict
        :return:
            A generatory of :class:`EventDatum` objects.

        """
        # Skip header
        data.seek(0)
        data.readline()
        data.readline()

        for line in data:
            values = line.split()
            time = int(values[0])
            tcp_type = values[1]  # connect, accept, or close
            source_pid = int(values[2])
            source_comm = values[3]
            source_addr = values[5]
            dest_addr = values[6]
            source_port = int(values[7])
            dest_port = int(values[8])
            net_ns = int(values[9])

            # Discard external TCP
            if not source_addr.startswith("127."):
                continue
            elif not dest_addr.startswith("127."):
                continue
            elif self.options and self.options.net_ns != net_ns:
                continue

            # Get destination PIDs from port_lookup dictionary
            if dest_port not in port_lookup:
                output.error_(
                    text="IPC: Could not find destination port PID/comm. "
                         "Check log for details.",
                    description="Could not find destination port PID/comm: "
                                "Time: {}  Type: {}  Source PID: {}  "
                                "Source comm: {}  Source port : {}  "
                                "Dest port: {}  Net namespace: {}"
                                .format(time, tcp_type, source_pid, source_comm,
                                        source_port, dest_port, net_ns)
                )
                continue

            dest_pids = port_lookup[dest_port]

            # Drop if there are multiple possible PIDs
            if len(dest_pids) != 1:
                output.error_(
                    text="IPC: Too many destination port PIDs/comms found. "
                         "Check log for details.",
                    description="Too many destination port PIDs/comms found: "
                                "Time: {}  Type: {}  Source PID: {}  "
                                "Source comm: {}  Source port : {}  "
                                "Dest (port, comm) pairs: {}  Net namespace: {}"
                                .format(time, tcp_type, source_pid, source_comm,
                                        source_port, str(sorted(dest_pids)),
                                        net_ns)
                )
                continue

            dest_pid, dest_comm = dest_pids.pop()
            dest_pids.add((dest_pid, dest_comm))  # Ensure set isn't altered

            # Otherwise output event
            event = data_io.EventDatum(time=time, type=tcp_type,
                                       specific_datum=(
                                             source_pid, source_comm,
                                             source_port,
                                             dest_pid, dest_comm, dest_port,
                                             net_ns)
                                       )

            yield event
