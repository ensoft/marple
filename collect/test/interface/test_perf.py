# -------------------------------------------------------------
# test_perf.py - tests for interaction with perf
# July-August 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

""" Test perf interactions and stack parsing. """

import unittest
from unittest import mock

from collect.interface import perf
from common import datatypes


class _PerfCollecterBaseTest(unittest.TestCase):
    """
    Base test for perf data collection testing.

    Mocks out subprocess and logging for all tests by overriding run().
    Sets useful class variables.

    """

    time = 5

    def run(self, result=None):
        with mock.patch('collect.interface.perf.subprocess') as subproc_mock, \
             mock.patch('collect.interface.perf.logger') as log_mock:
            self.subproc_mock = subproc_mock
            self.log_mock = log_mock
            self.subproc_mock.Popen.return_value.communicate.side_effect = \
                [(b"test_out1", b"test_err1"), (b"test_out2", b"test_err2"),
                 (b"test_out3", b"test_err3"), (b"test_out4", b"test_err4")]
            self.pipe_mock = self.subproc_mock.PIPE
            super().run(result)


class MemoryEventsTest(_PerfCollecterBaseTest):
    """ Test memory event collection. """
    @mock.patch('collect.interface.perf.StackParser')
    def test(self, stack_parse_mock):
        collecter = perf.MemoryEvents(self.time, None)
        collecter.collect()

        expected_calls = [
            mock.call(['perf', 'record', '-ag', '-e',
                       "'{mem-loads,mem-stores}'", 'sleep', str(self.time)],
                      stderr=self.pipe_mock),
            mock.call().communicate(),
            mock.call(['perf', 'script'], stdout=self.pipe_mock,
                      stderr=self.pipe_mock),
            mock.call().communicate()

        ]

        self.subproc_mock.Popen.assert_has_calls(expected_calls)

        expected_logs = [
            mock.call("test_err1"),
            mock.call("test_err2")
        ]
        self.log_mock.error.assert_has_calls(expected_logs)

        stack_parse_mock.assert_called_once_with("test_out2")
        stack_parse_mock.return_value.stack_collapse.assert_called_once_with()


class MemoryMallocTest(_PerfCollecterBaseTest):
    """ Test memory malloc probe collection. """
    @mock.patch('collect.interface.perf.StackParser')
    def test(self, stack_parse_mock):
        collecter = perf.MemoryMalloc(self.time, None)
        collecter.collect()

        expected_calls = [
            mock.call(['perf', 'probe', '-q', '--del', '*malloc*'],
                      stderr=self.pipe_mock),
            mock.call().communicate(),
            mock.call(["perf", "probe", "-qx", "/lib*/*/libc.so.*",
                       "malloc:1 size=%di"], stderr=self.pipe_mock),
            mock.call().communicate(),
            mock.call(['perf', 'record', '-ag', '-e', 'probe_libc:malloc:',
                       'sleep', str(self.time)], stderr=self.pipe_mock),
            mock.call().communicate(),
            mock.call(['perf', 'script'], stdout=self.pipe_mock,
                      stderr=self.pipe_mock),
            mock.call().communicate()
        ]

        self.subproc_mock.Popen.assert_has_calls(expected_calls)

        expected_logs = [
            mock.call("test_err1"),
            mock.call("test_err2"),
            mock.call("test_err3"),
            mock.call("test_err4")
        ]
        self.log_mock.error.assert_has_calls(expected_logs)

        stack_parse_mock.assert_called_once_with("test_out4")
        stack_parse_mock.return_value.stack_collapse.assert_called_once_with()


class StackTraceTest(_PerfCollecterBaseTest):
    """ Test stack trace collection. """
    @mock.patch('collect.interface.perf.StackParser')
    def test(self, stack_parse_mock):
        options = perf.StackTrace.Options(frequency=1, cpufilter="filter")
        collecter = perf.StackTrace(self.time, options)
        collecter.collect()

        expected_calls = [
            mock.call(['perf', 'record', '-F', str(options.frequency),
                       options.cpufilter, '-g', '--', 'sleep', str(self.time)],
                      stderr=self.pipe_mock),
            mock.call().communicate(),
            mock.call(['perf', 'script'], stdout=self.pipe_mock,
                      stderr=self.pipe_mock),
            mock.call().communicate()
        ]

        self.subproc_mock.Popen.assert_has_calls(expected_calls)

        expected_logs = [
            mock.call("test_err1"),
            mock.call("test_err2"),
        ]
        self.log_mock.error.assert_has_calls(expected_logs)

        stack_parse_mock.assert_called_once_with("test_out2")
        stack_parse_mock.return_value.stack_collapse.assert_called_once_with()


class SchedulingEventsTest(_PerfCollecterBaseTest):
    """ Test scheduling event collection. """
    @mock.patch('collect.interface.perf.re')
    def test_success(self, re_mock):
        """ Test successful regex matching. """
        # Set up mocks
        match_mock = re_mock.match.return_value
        match_mock.group.side_effect = [
            "111.999",
            "test_name",
            "test_pid",
            "4",
            "test_event"
        ]

        collecter = perf.SchedulingEvents(self.time, None)
        sched_events = list(collecter.collect())

        expected_calls = [
            mock.call(['perf', 'sched', 'record', 'sleep',
                       str(self.time)], stderr=self.pipe_mock),
            mock.call().communicate(),
            mock.call(['perf', 'sched', 'script', '-F',
                       'comm,pid,cpu,time,event'],
                      stdout=self.pipe_mock, stderr=self.pipe_mock),
            mock.call().communicate()
        ]

        self.subproc_mock.Popen.assert_has_calls(expected_calls)

        expected_logs = [
            mock.call("test_err1"),
            mock.call("test_err2")
        ]

        self.log_mock.error.assert_has_calls(expected_logs)

        re_mock.match.assert_called_once_with(r"\s*"
                                              r"(?P<name>\S+(\s+\S+)*)\s+"
                                              r"(?P<pid>\d+)\s+"
                                              r"\[(?P<cpu>\d+)\]\s+"
                                              r"(?P<time>\d+.\d+):\s+"
                                              r"(?P<event>\S+)",
                                              "test_out2")

        expected_event = datatypes.SchedEvent(datum="test_name (pid: test_pid)",
                                              track="cpu 4",
                                              time=111000999,
                                              type="test_event")

        self.assertIn(expected_event, sched_events)

    @mock.patch('collect.interface.perf.re')
    def test_no_match(self, re_mock):
        """ Test failed regex matching. """
        # Set up mocks
        re_mock.match.return_value = None

        collecter = perf.SchedulingEvents(self.time, None)
        sched_events = list(collecter.collect())

        expected_calls = [
            mock.call(['perf', 'sched', 'record', 'sleep',
                       str(self.time)], stderr=self.pipe_mock),
            mock.call().communicate(),
            mock.call(['perf', 'sched', 'script', '-F',
                       'comm,pid,cpu,time,event'],
                      stdout=self.pipe_mock, stderr=self.pipe_mock),
            mock.call().communicate()
        ]

        self.subproc_mock.Popen.assert_has_calls(expected_calls)

        expected_logs = [
            mock.call("test_err1"),
            mock.call("test_err2"),
            mock.call("Failed to parse event data: %s Expected format: name "
                      "pid cpu time event", "test_out2")
        ]

        self.log_mock.error.assert_has_calls(expected_logs)

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
    @mock.patch('collect.interface.perf.StackParser')
    def test(self, stack_parse_mock):
        collecter = perf.DiskBlockRequests(self.time, None)
        collecter.collect()

        expected_calls = [
            mock.call(['perf', 'record', '-ag', '-e', 'block:block_rq_insert',
                       'sleep', str(self.time)], stderr=self.pipe_mock),
            mock.call().communicate(),
            mock.call(['perf', 'script'], stderr=self.pipe_mock,
                      stdout=self.pipe_mock),
            mock.call().communicate()
        ]

        self.subproc_mock.Popen.assert_has_calls(expected_calls)

        expected_logs = [
            mock.call("test_err1"),
            mock.call("test_err2")
        ]

        self.log_mock.error.assert_has_calls(expected_logs)

        stack_parse_mock.assert_called_once_with("test_out2")
        stack_parse_mock.return_value.stack_collapse.assert_called_once_with()


class StackParserTest(unittest.TestCase):
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

    @mock.patch("collect.interface.perf.INCLUDE_PID", True)
    def test_parse_baseline_pid(self):
        """Tests creation of pname with pid."""
        self.stack_parser._parse_baseline(line="java 27 464.116: cycles:")
        self.assertTrue(self.stack_parser._pname == "java-27")

    @mock.patch("collect.interface.perf.INCLUDE_TID", True)
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
        expected = [datatypes.StackData(weight=1, stack=(
            "swapper", "secondary_startup_64", "start_secondary",
            "cpu_startup_entry", "call_cpuidle", "do_idle", "cpuidle_enter",
            "cpuidle_enter_state", "intel_idle"))]

        # # Mock a file with sample data
        # file_mock = StringIO("")
        # file_mock.writelines(sample_stack)
        # context_mock =  open_mock.return_value
        # context_mock.__enter__.return_value = file_mock

        self.stack_parser.data = sample_stack
        self.stack_parser.event_filter = ""

        # Run the whole stack_collapse function
        events = list(self.stack_parser.stack_collapse())

        self.assertEqual(expected, events)
