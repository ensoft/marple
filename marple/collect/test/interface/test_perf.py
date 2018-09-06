# -------------------------------------------------------------
# test_perf.py - tests for interaction with perf
# July-August 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

""" Test perf interactions and stack parsing. """

import asynctest
from io import StringIO
from marple.collect.interface import perf
from marple.common import data_io


class _PerfCollecterBaseTest(asynctest.TestCase):
    """
    Base test for perf data collection testing.

    Mocks out subprocess and logging for all tests by overriding run().
    Sets useful class variables.

    """

    time = 5
    async_mock, log_mock, pipe_mock, create_mock, strio_mock = \
        None, None, None, None, None

    def run(self, result=None):
        with asynctest.patch('marple.collect.interface.perf.asyncio') as async_mock, \
             asynctest.patch('marple.collect.interface.perf.logger') as log_mock, \
             asynctest.patch('marple.collect.interface.perf.os') as os_mock, \
             asynctest.patch('marple.collect.interface.perf.StringIO') as strio_mock:
            self.async_mock = async_mock

            # Set up subprocess mocks
            self.create_mock = asynctest.CoroutineMock()
            async_mock.create_subprocess_shell = self.create_mock

            # Set up communicate mocks
            comm_mock = asynctest.CoroutineMock()
            comm_mock.side_effect = [(b"test_out1", b"test_err1"),
                                     (b"test_out2", b"test_err2"),
                                     (b"test_out3", b"test_err3"),
                                     (b"test_out4", b"test_err4")]
            self.create_mock.return_value.communicate = comm_mock

            # Set up other mocks
            self.log_mock = log_mock
            self.pipe_mock = async_mock.subprocess.PIPE
            self.os_mock = os_mock
            self.strio_mock = strio_mock

            super().run(result)


class MemoryEventsTest(_PerfCollecterBaseTest):
    """ Test memory event collection. """
    @asynctest.patch('marple.collect.interface.perf.StackParser')
    async def test(self, stack_parse_mock):
        collecter = perf.MemoryEvents(self.time, None)
        await collecter.collect()

        self.create_mock.assert_has_calls([
            asynctest.call(
                "perf record -ag -o " + perf.MemoryEvents._PERF_FILE_NAME +
                " -e '{mem-loads,mem-stores}' sleep " +
                str(self.time), stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "perf script -i " + perf.MemoryEvents._PERF_FILE_NAME,
                stdout=self.pipe_mock,
                stderr=self.pipe_mock),
            asynctest.call().communicate()
        ])

        self.log_mock.error.assert_has_calls([
            asynctest.call('test_err1'),
            asynctest.call('test_err2')
        ])

        self.os_mock.remove.assert_called_once_with(
            self.os_mock.getcwd.return_value + "/" +
            perf.MemoryEvents._PERF_FILE_NAME
        )

        self.strio_mock.assert_called_once_with('test_out2')
        stack_parse_mock.assert_called_once_with(self.strio_mock('test_out2'))
        stack_parse_mock.return_value.stack_collapse.assert_called_once_with()


class MemoryMallocTest(_PerfCollecterBaseTest):
    """ Test memory malloc probe collection. """
    @asynctest.patch('marple.collect.interface.perf.StackParser')
    async def test(self, stack_parse_mock):
        collecter = perf.MemoryMalloc(self.time, None)
        await collecter.collect()

        self.create_mock.assert_has_calls([
            asynctest.call(
                "perf probe -q --del *malloc*", stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "perf probe -qx /lib*/*/libc.so.* malloc:1 size=%di",
                stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "perf record -ag -o " + perf.MemoryMalloc._PERF_FILE_NAME +
                " -e probe_libc:malloc: sleep " + str(self.time),
                stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "perf script -i " + perf.MemoryMalloc._PERF_FILE_NAME,
                stdout=self.pipe_mock, stderr=self.pipe_mock),
            asynctest.call().communicate()
        ])

        self.log_mock.error.assert_has_calls([
            asynctest.call("test_err1"),
            asynctest.call("test_err2"),
            asynctest.call("test_err3"),
            asynctest.call("test_err4")
        ])

        self.os_mock.remove.assert_called_once_with(
            self.os_mock.getcwd.return_value + "/" +
            perf.MemoryMalloc._PERF_FILE_NAME
        )

        self.strio_mock.assert_called_once_with('test_out4')
        stack_parse_mock.assert_called_once_with(self.strio_mock('test_out4'))
        stack_parse_mock.return_value.stack_collapse.assert_called_once_with()


class StackTraceTest(_PerfCollecterBaseTest):
    """ Test stack trace collection. """
    @asynctest.patch('marple.collect.interface.perf.StackParser')
    async def test(self, stack_parse_mock):
        options = perf.StackTrace.Options(frequency=1, cpufilter="filter")
        collecter = perf.StackTrace(self.time, options)
        await collecter.collect()

        self.create_mock.assert_has_calls([
            asynctest.call(
                "perf record -F " + str(options.frequency) + " " +
                options.cpufilter + " -g -o " +
                perf.StackTrace._PERF_FILE_NAME + " -- sleep " + str(self.time),
                stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "perf script -i " + perf.StackTrace._PERF_FILE_NAME,
                stdout=self.pipe_mock, stderr=self.pipe_mock),
            asynctest.call().communicate()
        ])

        expected_logs = [

        ]
        self.log_mock.error.assert_has_calls([
            asynctest.call('test_err1'),
            asynctest.call('test_err2')
        ])

        self.os_mock.remove.assert_called_once_with(
            self.os_mock.getcwd.return_value + "/" +
            perf.StackTrace._PERF_FILE_NAME
        )

        self.strio_mock.assert_called_once_with('test_out2')
        stack_parse_mock.assert_called_once_with(self.strio_mock('test_out2'))
        stack_parse_mock.return_value.stack_collapse.assert_called_once_with()


class SchedulingEventsTest(_PerfCollecterBaseTest):
    """ Test scheduling event collection. """
    @asynctest.patch('marple.collect.interface.perf.re')
    async def test_success(self, re_mock):
        """ Test successful regex matching. """
        # Set up mocks
        self.strio_mock.return_value = StringIO('test_out2')
        match_mock = re_mock.match.return_value
        match_mock.group.side_effect = [
            "111.999",
            "test_name",
            "test_pid",
            "4",
            "test_event"
        ]

        collecter = perf.SchedulingEvents(self.time)
        data = await collecter.collect()
        sched_events = list(data.datum_generator)

        self.create_mock.assert_has_calls([
            asynctest.call(
                "perf sched record -o " +
                perf.SchedulingEvents._PERF_FILE_NAME +
                " sleep " + str(self.time), stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "perf sched script -i " +
                perf.SchedulingEvents._PERF_FILE_NAME +
                " -F 'comm,pid,cpu,time,event'",
                stdout=self.pipe_mock, stderr=self.pipe_mock),
            asynctest.call().communicate()
        ])

        self.log_mock.error.assert_has_calls([
            asynctest.call("test_err1"),
            asynctest.call("test_err2")
        ])

        self.os_mock.remove.assert_called_once_with(
            self.os_mock.getcwd.return_value + "/" +
            perf.SchedulingEvents._PERF_FILE_NAME
        )

        re_mock.match.assert_called_once_with(r"\s*"
                                              r"(?P<name>\S+(\s+\S+)*)\s+"
                                              r"(?P<pid>\d+)\s+"
                                              r"\[(?P<cpu>\d+)\]\s+"
                                              r"(?P<time>\d+.\d+):\s+"
                                              r"(?P<event>\S+)",
                                              "test_out2")

        expected_event = data_io.EventDatum(
            specific_datum=("test_name (pid: test_pid)", "cpu 4"),
            time=111000999, type="test_event"
        )

        self.assertEqual([expected_event], sched_events)

    @asynctest.patch('marple.collect.interface.perf.re')
    async def test_no_match(self, re_mock):
        """ Test failed regex matching. """
        # Set up mocks
        self.strio_mock.return_value = StringIO('test_out2')
        re_mock.match.return_value = None

        collecter = perf.SchedulingEvents(self.time, None)
        data = await collecter.collect()
        sched_events = list(data.datum_generator)

        self.create_mock.assert_has_calls([
            asynctest.call(
                "perf sched record -o " +
                perf.SchedulingEvents._PERF_FILE_NAME +
                " sleep " + str(self.time), stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "perf sched script -i " +
                perf.SchedulingEvents._PERF_FILE_NAME +
                " -F 'comm,pid,cpu,time,event'",
                stdout=self.pipe_mock, stderr=self.pipe_mock),
            asynctest.call().communicate()
        ])

        self.log_mock.error.assert_has_calls([
            asynctest.call("test_err1"),
            asynctest.call("test_err2")
        ])

        self.os_mock.remove.assert_called_once_with(
            self.os_mock.getcwd.return_value + "/" +
            perf.SchedulingEvents._PERF_FILE_NAME
        )

        re_mock.match.assert_called_once_with(r"\s*"
                                              r"(?P<name>\S+(\s+\S+)*)\s+"
                                              r"(?P<pid>\d+)\s+"
                                              r"\[(?P<cpu>\d+)\]\s+"
                                              r"(?P<time>\d+.\d+):\s+"
                                              r"(?P<event>\S+)",
                                              "test_out2")

        self.assertEqual([], sched_events)


class DiskBlockRequestsTest(_PerfCollecterBaseTest):
    """ Test disk block request data collection. """
    @asynctest.patch('marple.collect.interface.perf.StackParser')
    async def test(self, stack_parse_mock):
        collecter = perf.DiskBlockRequests(self.time, None)
        await collecter.collect()

        self.create_mock.assert_has_calls([
            asynctest.call(
                "perf record -ag -o " + perf.DiskBlockRequests._PERF_FILE_NAME +
                " -e block:block_rq_insert sleep " + str(self.time),
                stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "perf script -i " + perf.DiskBlockRequests._PERF_FILE_NAME,
                stdout=self.pipe_mock, stderr=self.pipe_mock),
            asynctest.call().communicate()
        ])

        self.log_mock.error.assert_has_calls([
            asynctest.call("test_err1"),
            asynctest.call("test_err2")
        ])

        self.os_mock.remove.assert_called_once_with(
            self.os_mock.getcwd.return_value + "/" +
            perf.DiskBlockRequests._PERF_FILE_NAME
        )

        self.strio_mock.assert_called_once_with('test_out2')
        stack_parse_mock.assert_called_once_with(self.strio_mock('test_out2'))
        stack_parse_mock.return_value.stack_collapse.assert_called_once_with()


class StackParserTest(asynctest.TestCase):
    """Test class for the StackParser class."""
    def setUp(self):
        """Creates a generic empty StackParser object."""
        super().setUp()
        self.stack_parser = perf.StackParser("")

    def tearDown(self):
        """Deallocates the StackParser object"""
        super().tearDown()
        self.stack_parser = None

    def test_is_empty(self):
        """Tests the function recognising an empty line."""
        self.assertTrue(self.stack_parser._line_is_empty(""))

    def test_is_empty_neg(self):
        """Tests that the line_is_empty function recognises non empty lines."""
        self.assertFalse(self.stack_parser._line_is_empty(" Not empty "))

    def test_is_baseline(self):
        """Tests the function recognising a baseline."""
        # Variations of baselines
        baselines = ["java 25607 4794564.109216: cycles:",
                     "java 12688 [002] 6544038.708352: cpu-clock:",
                     "V8 WorkerThread 25607 4794564.109216: cycles:",
                     "java 24636/25607 [000] 4794564.109216: cycles:",
                     "java 12688/12764 6544038.708352: cpu-clock:",
                     "V8 WorkerThread 24636/25607 [000] 94564.109216: cycles:"]
        for line in baselines:
            self.assertTrue(self.stack_parser._line_is_baseline(line))

    def test_is_stackline(self):
        """Tests the function recognising a stackline."""
        # Variations of stacklines
        stacklines = \
            ["	ffffffffa01bbd11 __perf_event_enable ([kernel.kallsyms])",
             "  ffffffffa01b45bb event_function ([kernel.kallsyms])     ",
             "  142cb9 [unknown] (/usr/lib/linux-tools-4.15.0-24/perf)"
             "  21b97 __libc_start_main (/lib/x86_64-linux-gnu/libc-2.27.so)"
             "2e46258d4c544155 [unknown] ([unknown])"]

        for line in stacklines:
            self.assertTrue(self.stack_parser._line_is_stackline(line))

    def test_parse_baseline_pname_only(self):
        """Tests the extraction of process names in _parse_baseline."""
        # Check that a simple process name is extracted correctly
        self.stack_parser._parse_baseline(line="java 27 464.116: cycles:")
        self.assertTrue(self.stack_parser._pname == "java")

        # Check that a space separated process name gets space replaced by _
        self.stack_parser._parse_baseline(line="V8 WorkerThread 27 464.116: "
                                               "cycles:")
        self.assertTrue(self.stack_parser._pname == "V8_WorkerThread")

        # Check that the event_filter defaulted:
        self.assertTrue(self.stack_parser.event_filter == "cycles")

    @asynctest.patch("marple.collect.interface.perf.INCLUDE_PID", True)
    def test_parse_baseline_pid(self):
        """Tests creation of pname with pid."""
        self.stack_parser._parse_baseline(line="java 27 464.116: cycles:")
        self.assertTrue(self.stack_parser._pname == "java-27")

    @asynctest.patch("marple.collect.interface.perf.INCLUDE_TID", True)
    def test_parse_baseline_tid(self):
        """Tests creation of pname with pid and tid."""
        self.stack_parser._parse_baseline(line="java 27/1 464.116: cycles:")
        self.assertTrue(self.stack_parser._pname == "java-27/1")

    def test_parse_stackline(self):
        """Tests the insertion of stacklines in the stack array"""
        self.stack_parser._pname = "some_process"
        self.stack_parser._parse_stackline(line="ffffffffabe0c31d "
                                                "intel_pmu_enable_ (["
                                                "kernel.kallsyms])")

        self.assertTrue(self.stack_parser._stack == ["intel_pmu_enable_"])

    def test_make_stack(self):
        """Tests that a stack is correctly created from lines list and pname."""
        # Example data
        pname = "some_process"
        stacklines = ["call1", "call2"]

        # Expected output
        expected = tuple([pname] + stacklines)

        # Pass example data to stack parser
        self.stack_parser._pname = pname
        self.stack_parser._stack = stacklines

        # Run the stack maker function
        stackfolded = self.stack_parser._make_stack()

        self.assertTrue(stackfolded == expected)

    def test_StackParser_complete(self):

        # Example of a single stack from perf extracted stack data
        sample_stack = \
            "swapper     0 [003] 687886.672908:  108724462 cycles:ppp:\n" \
            "ffffffffa099768b intel_idle ([kernel.kallsyms])\n" \
            "ffffffffa07e5ce4 cpuidle_enter_state ([kernel.kallsyms])\n" \
            "ffffffffa07e5f97 cpuidle_enter ([kernel.kallsyms])\n" \
            "ffffffffa00d299c do_idle ([kernel.kallsyms])\n" \
            "ffffffffa00d2723 call_cpuidle ([kernel.kallsyms])\n" \
            "ffffffffa00d2be3 cpu_startup_entry ([kernel.kallsyms])\n" \
            "ffffffffa00581cb start_secondary ([kernel.kallsyms])\n" \
            "ffffffffa00000d5 secondary_startup_64 ([kernel.kallsyms])\n" \
            "\n"

        # Expected output data
        expected = [data_io.StackDatum(weight=1, stack=(
            "swapper", "secondary_startup_64", "start_secondary",
            "cpu_startup_entry", "call_cpuidle", "do_idle", "cpuidle_enter",
            "cpuidle_enter_state", "intel_idle"))]

        # # Mock a file with sample data
        # file_mock = StringIO("")
        # file_mock.writelines(sample_stack)
        # context_mock =  open_mock.return_value
        # context_mock.__enter__.return_value = file_mock

        self.stack_parser.data = StringIO(sample_stack)
        self.stack_parser.event_filter = ""

        # Run the whole stack_collapse function
        events = list(self.stack_parser.stack_collapse())

        self.assertEqual(expected, events)
