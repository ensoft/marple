# -------------------------------------------------------------
# test_ebpf.py - tests for interactions with the bcc/eBPF module
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

""" Test bcc/ebpf interactions and stack parsing. """

import subprocess
import unittest
from io import StringIO
from unittest import mock

from collect.interface import ebpf
from common import datatypes


class Mallocstacks(unittest.TestCase):
    """
    Class that tests the mallocstacks interface

    """

    @staticmethod
    def to_kilo(num):
        """
        Helper function, transforms from bytes to kilobytes
        :param num: number of bytes
        :return: closest into to the actual number of kilobytes

        """
        return int(num / 1000)

    @staticmethod
    def mock(mock_ret):
        """
        Helper method for the testing of collect

        :param mock_ret: stdout mock value
        :returns gen: generator of StackData objects, based on what mock_ret is
        """
        with mock.patch("subprocess.Popen") as popenmock:
            popenmock().communicate.return_value = (mock_ret,
                                                    b"")
            ms_obj = ebpf.MallocStacks(100)
            gen = ms_obj.collect()

            return [stack_data for stack_data in gen]

    def test_basic_collect(self):
        """
        Basic test case where everything should work as expected

        """
        mock_return_popen_stdout = b"123123#proc1#func1#func2\n321321#proc2#" \
                                   b"func1#func2#func3\n"

        expected = [datatypes.StackData(self.to_kilo(123123),
                                        ("proc1", "func1", "func2")),
                    datatypes.StackData(self.to_kilo(321321),
                                        ("proc2", "func1", "func2", "func3"))]

        output = self.mock(mock_return_popen_stdout)
        self.assertEqual(output, expected)

    def test_strange_symbols(self):
        """
        Basic test case where everything should work as expected

        """
        mock_return_popen_stdout = b"123123#1   [];'#[]-=1   2=\n"

        expected = [datatypes.StackData(self.to_kilo(123123),
                                        ("1   [];'", "[]-=1   2="))]

        output = self.mock(mock_return_popen_stdout)
        self.assertEqual(output, expected)

    def test_nan(self):
        """
        Tests if the weight is not a number the exception is raised correctly

        """
        mock_return_popen_stdout = b"NOTANUMBER#abcd#abcd\n"
        with self.assertRaises(ValueError):
            output = self.mock(mock_return_popen_stdout)


class TCPTracerTest(unittest.TestCase):
    time = 5

    @mock.patch('collect.interface.ebpf.subprocess')
    @mock.patch('collect.interface.ebpf.logger')
    @mock.patch('collect.interface.ebpf.os')
    @mock.patch('collect.interface.ebpf.TCPTracer._generate_dict')
    @mock.patch('collect.interface.ebpf.TCPTracer._generate_events')
    def test_collect_normal(self, gen_events_mock, gen_dict_mock, os_mock,
                            log_mock, proc_mock):
        """
        Test normal operation, when tcptracer outputs KeyboardInterrupt only

        """
        communicate_mock = proc_mock.Popen.return_value.communicate
        communicate_mock.side_effect = [
            (b'output', b'Traceback (most recent call last):\nstacktrace'
                        b'\nstacktrace etc.\nKeyboardInterrupt\n')]
        pipe_mock = proc_mock.PIPE

        collecter = ebpf.TCPTracer(self.time, None)
        collecter.collect()

        proc_mock.Popen.assert_called_once_with(
            [ebpf.BCC_TOOLS_PATH + 'tcptracer -tv'],
            shell=True, stdout=pipe_mock, stderr=pipe_mock,
            preexec_fn=os_mock.setsid)

        communicate_mock.assert_called_once_with(timeout=self.time)

        log_mock.error.assert_has_calls([])

        gen_dict_mock.assert_called_once()
        gen_events_mock.assert_called_once()

    @mock.patch('collect.interface.ebpf.subprocess')
    @mock.patch('collect.interface.ebpf.logger')
    @mock.patch('collect.interface.ebpf.os')
    @mock.patch('collect.interface.ebpf.TCPTracer._generate_dict')
    @mock.patch('collect.interface.ebpf.TCPTracer._generate_events')
    def test_collect_error(self, gen_events_mock, gen_dict_mock, os_mock,
                           log_mock, proc_mock):
        """
        Test error operation, when tcptracer outputs an error

        """
        communicate_mock = proc_mock.Popen.return_value.communicate
        communicate_mock.side_effect = [
            (b'output', b'Traceback (most recent call last):\nstacktrace'
                        b'\nstacktrace etc.\nKeyboardInterrupt\nERROR')]
        pipe_mock = proc_mock.PIPE

        collecter = ebpf.TCPTracer(self.time, None)
        collecter.collect()

        proc_mock.Popen.assert_called_once_with(
            [ebpf.BCC_TOOLS_PATH + 'tcptracer -tv'],
            shell=True, stdout=pipe_mock, stderr=pipe_mock,
            preexec_fn=os_mock.setsid)

        communicate_mock.assert_called_once_with(timeout=self.time)

        log_mock.error.assert_called_once_with(
            'Traceback (most recent call last):\nstacktrace'
            '\nstacktrace etc.\nKeyboardInterrupt\nERROR')

        gen_dict_mock.assert_called_once()
        gen_events_mock.assert_called_once()

    @mock.patch('collect.interface.ebpf.subprocess.Popen')
    @mock.patch('collect.interface.ebpf.subprocess.PIPE')
    @mock.patch('collect.interface.ebpf.logger')
    @mock.patch('collect.interface.ebpf.os')
    @mock.patch('collect.interface.ebpf.TCPTracer._generate_dict')
    @mock.patch('collect.interface.ebpf.TCPTracer._generate_events')
    def test_collect_timeout_normal(self, gen_events_mock, gen_dict_mock, os_mock,
                             log_mock, pipe_mock, popen_mock):
        """
        Test when subprocess communicate times out under normal
        operation, when tcptracer outputs KeyboardInterrupt only

        """
        communicate_mock = popen_mock.return_value.communicate
        communicate_mock.side_effect = [
            subprocess.TimeoutExpired('cmd', self.time),
            (b'output', b'Traceback (most recent call last):\nstacktrace'
                        b'\nstacktrace etc.\nKeyboardInterrupt\n')]

        collecter = ebpf.TCPTracer(self.time, None)
        collecter.collect()

        popen_mock.assert_called_once_with(
            [ebpf.BCC_TOOLS_PATH + 'tcptracer -tv'],
            shell=True, stdout=pipe_mock, stderr=pipe_mock,
            preexec_fn=os_mock.setsid)

        communicate_mock.assert_has_calls([
            mock.call(timeout=self.time),
            mock.call()
        ])

        log_mock.error.assert_has_calls([])

        gen_dict_mock.assert_called_once()
        gen_events_mock.assert_called_once()

    @mock.patch('collect.interface.ebpf.subprocess.Popen')
    @mock.patch('collect.interface.ebpf.subprocess.PIPE')
    @mock.patch('collect.interface.ebpf.logger')
    @mock.patch('collect.interface.ebpf.os')
    @mock.patch('collect.interface.ebpf.TCPTracer._generate_dict')
    @mock.patch('collect.interface.ebpf.TCPTracer._generate_events')
    def test_collect_timeout_error(self, gen_events_mock, gen_dict_mock, os_mock,
                             log_mock, pipe_mock, popen_mock):
        """
        Test when subprocess communicate times out under error
        operation, when tcptracer outputs error

        """
        communicate_mock = popen_mock.return_value.communicate
        communicate_mock.side_effect = [
            subprocess.TimeoutExpired('cmd', self.time),
            (b'output', b'Traceback (most recent call last):\nstacktrace'
                        b'\nstacktrace etc.\nKeyboardInterrupt\nERROR')]

        collecter = ebpf.TCPTracer(self.time, None)
        collecter.collect()

        popen_mock.assert_called_once_with(
            [ebpf.BCC_TOOLS_PATH + 'tcptracer -tv'],
            shell=True, stdout=pipe_mock, stderr=pipe_mock,
            preexec_fn=os_mock.setsid)

        communicate_mock.assert_has_calls([
            mock.call(timeout=self.time),
            mock.call()
        ])

        log_mock.error.assert_called_once_with(
            'Traceback (most recent call last):\nstacktrace'
            '\nstacktrace etc.\nKeyboardInterrupt\nERROR')

        gen_dict_mock.assert_called_once()
        gen_events_mock.assert_called_once()

    def test_generate_dict_empty(self):
        """ Test _generate_dict with empty data"""
        tracer = object.__new__(ebpf.TCPTracer)
        data = StringIO(
            "header1\nheader2\n"
        )
        result = tracer._generate_dict(data)
        self.assertEqual({}, result)

    def test_generate_dict_single(self):
        """ Test _generate_dict with single entries for each port """
        tracer = object.__new__(ebpf.TCPTracer)
        tracer.options = None
        data = StringIO(
            "header1\n"
            "time type pid comm   ip  s_addr d_addr s_port d_port netns\n"
            "1    A    2   comm1  4   127.   127.   3      4      5\n"
            "6    B    7   comm2  4   127.   127.   4      3      5\n"
            "1    A    2   comm3  4   x      x      3      4      5\n"
        )

        expected = {3: {(2, 'comm1')}, 4: {(7, 'comm2')}}
        result = tracer._generate_dict(data)
        self.assertEqual(expected, result)

    def test_generate_dict_single_ns(self):
        """
        Test _generate_dict with single entries for each port, allowing
        only a single namespace

        """
        tracer = object.__new__(ebpf.TCPTracer)
        tracer.options = ebpf.TCPTracer.Options(5)
        data = StringIO(
            "header1\n"
            "time type pid comm   ip  s_addr d_addr s_port d_port netns\n"
            "1    A    2   comm1  4   127.   127.   3      4      5\n"
            "6    B    7   comm2  4   127.   127.   4      3      5\n"
            "6    B    8   comm4  4   127.   127.   4      3      6\n"
            "1    A    2   comm3  4   x      x      3      4      5\n"
        )

        expected = {3: {(2, 'comm1')}, 4: {(7, 'comm2')}}
        result = tracer._generate_dict(data)
        self.assertEqual(expected, result)

    def test_generate_dict_multiple(self):
        """ Test _generate_dict with multiple entries for a port """
        tracer = object.__new__(ebpf.TCPTracer)
        tracer.options = None
        data = StringIO(
            "header1\n"
            "time type pid comm   ip  s_addr d_addr s_port d_port netns\n"
            "1    A    2   comm1  4   127.   127.   3      4      5\n"
            "6    B    7   comm2  4   127.   127.   4      3      5\n"
            "7    C    8   comm4  4   127.   127.   4      2      5\n"
            "1    A    2   comm3  4   x      x      3      4      5\n"
        )

        expected = {3: {(2, 'comm1')}, 4: {(7, 'comm2'), (8, 'comm4')}}
        result = tracer._generate_dict(data)
        self.assertEqual(expected, result)

    def test_generate_dict_multiple_ns(self):
        """
        Test _generate_dict with multiple entries for a port, allowing
        only a single namespace

        """
        tracer = object.__new__(ebpf.TCPTracer)
        tracer.options = ebpf.TCPTracer.Options(5)
        data = StringIO(
            "header1\n"
            "time type pid comm   ip  s_addr d_addr s_port d_port netns\n"
            "1    A    2   comm1  4   127.   127.   3      4      5\n"
            "6    B    7   comm2  4   127.   127.   4      3      5\n"
            "7    C    8   comm4  4   127.   127.   4      2      5\n"
            "6    B    9   comm5  4   127.   127.   4      3      6\n"
            "1    A    2   comm3  4   x      x      3      4      5\n"
        )

        expected = {3: {(2, 'comm1')}, 4: {(7, 'comm2'), (8, 'comm4')}}
        result = tracer._generate_dict(data)
        self.assertEqual(expected, result)

    def test_generate_events_empty_data(self):
        """
        Test _generate_events with no data

        """
        tracer = object.__new__(ebpf.TCPTracer)
        data = StringIO(
            "header1\nheader2\n"
        )
        result = list(tracer._generate_events(data, {4: (1, 'comm')}))
        self.assertEqual([], result)

    @mock.patch('collect.interface.ebpf.output')
    def test_generate_events_empty_dict(self, output_mock):
        """
        Test _generate_events with no dict - tests failure to find port mapping

        """
        tracer = object.__new__(ebpf.TCPTracer)
        tracer.options = None
        data = StringIO(
            "header1\n"
            "time type pid comm   ip  s_addr d_addr s_port d_port netns\n"
            "1    A    2   comm1  4   127.   127.   3      4      5\n"
            "6    B    7   comm2  4   127.   127.   4      3      5\n"
            "1    A    2   comm3  4   x      x      3      4      5\n"
        )
        result = list(tracer._generate_events(data, {}))
        self.assertEqual([], result)
        expected_errors = [
            mock.call(
                    text="IPC: Could not find destination port PID/comm. "
                         "Check log for details.",
                    description="Could not find destination port PID/comm: "
                                "Time: 1  Type: A  Source PID: 2  "
                                "Source comm: comm1  Source port : 3  "
                                "Dest port: 4  Net namespace: 5"
            ),
            mock.call(
                text="IPC: Could not find destination port PID/comm. "
                     "Check log for details.",
                description="Could not find destination port PID/comm: "
                            "Time: 6  Type: B  Source PID: 7  "
                            "Source comm: comm2  Source port : 4  "
                            "Dest port: 3  Net namespace: 5"
            )
        ]
        output_mock.error_.assert_has_calls(expected_errors)

    def test_generate_events_normal(self):
        """
        Test _generate_events under normal operation, using all net namespaces

        """
        tracer = object.__new__(ebpf.TCPTracer)
        tracer.options = None
        data = StringIO(
            "header1\n"
            "time type pid comm   ip  s_addr d_addr s_port d_port netns\n"
            "1    A    2   comm1  4   127.   127.   3      4      5\n"
            "6    B    7   comm2  4   127.   127.   4      3      5\n"
            "1    A    2   comm3  4   x      x      3      4      5\n"
        )
        port_dict = {4: {('pid1', 'test1')}, 3: {('pid2', 'test2')}}
        result = list(tracer._generate_events(data, port_dict))
        expected = [
            datatypes.EventData(time=1, type='A',
                                specific_datum=(
                                    2, 'comm1', 3, 'pid1', 'test1', 4, 5)),
            datatypes.EventData(time=6, type='B',
                                specific_datum=(
                                    7, 'comm2', 4, 'pid2', 'test2', 3, 5))
        ]
        self.assertEqual(expected, result)

    @mock.patch('collect.interface.ebpf.output')
    def test_generate_events_full_dict(self, output_mock):
        """
        Test _generate_events under normal operation, using all net namespaces

        """
        tracer = object.__new__(ebpf.TCPTracer)
        tracer.options = None
        data = StringIO(
            "header1\n"
            "time type pid comm   ip  s_addr d_addr s_port d_port netns\n"
            "1    A    2   comm1  4   127.   127.   3      4      5\n"
            "6    B    7   comm2  4   127.   127.   4      3      5\n"
            "1    A    2   comm3  4   x      x      3      4      5\n"
        )
        port_dict = {4: {('pid1', 'test1')},
                     3: {('pid2', 'test2'), ('pid3', 'test3')}}
        result = list(tracer._generate_events(data, port_dict))
        expected = [
            datatypes.EventData(time=1, type='A',
                                specific_datum=(
                                    2, 'comm1', 3, 'pid1', 'test1', 4, 5)),
        ]
        self.assertEqual(expected, result)

        expected_errors = [
            mock.call(
                text="IPC: Too many destination port PIDs/comms found. "
                     "Check log for details.",
                description="Too many destination port PIDs/comms found: "
                            "Time: 6  Type: B  Source PID: 7  "
                            "Source comm: comm2  Source port : 4  "
                            "Dest (port, comm) pairs: "
                            "[('pid2', 'test2'), ('pid3', 'test3')]  "
                            "Net namespace: 5"
            )
        ]
        output_mock.error_.assert_has_calls(expected_errors)