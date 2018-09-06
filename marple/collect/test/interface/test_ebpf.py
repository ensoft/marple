# -------------------------------------------------------------
# test_ebpf.py - tests for interactions with the bcc/eBPF module
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

""" Test bcc/ebpf interactions and stack parsing. """

import asyncio
import asynctest
from io import StringIO


from marple.collect.interface import ebpf
from marple.common import data_io


class Mallocstacks(asynctest.TestCase):
    """
    Class that tests the mallocstacks interface

    """
    time = 5

    async def mock(self, out):
        """
        Helper method for mocking the mallocstqqacks.py subprocess.
        Also tests that the appropriate subprocess call is made.

        :param out:
            Desired stdout output for the subprocess.
        :return:
            A generator of StackDatum objects created from the desired output.

        """
        with asynctest.patch("marple.collect.interface.ebpf.asyncio") as async_mock:
            # Set up mocks
            create_mock = asynctest.CoroutineMock()
            async_mock.create_subprocess_exec = create_mock
            comm_mock = asynctest.CoroutineMock()
            comm_mock.side_effect = [(out, b'')]
            create_mock.return_value.communicate = comm_mock
            pipe_mock = async_mock.subprocess.PIPE

            # Run collecter
            gen = await ebpf.MallocStacks(self.time).collect()
            create_mock.assert_has_calls([
                asynctest.call(
                    'sudo', 'python', ebpf.BCC_TOOLS_PATH + 'mallocstacks.py',
                    '-f', str(self.time), stderr=pipe_mock, stdout=pipe_mock
                ),
                asynctest.call().communicate()
            ])

            return [datum for datum in gen.datum_generator]

    async def test_basic_collect(self):
        """
        Basic test case where everything should work as expected

        """
        mock_return_popen_stdout = b"123123$$$proc1;func1;func2\n" \
                                   b"321321$$$proc2;func1;func2;func3\n"

        expected = [data_io.StackDatum(123123,
                                       ("proc1", "func1", "func2")),
                    data_io.StackDatum(321321,
                                       ("proc2", "func1", "func2", "func3"))]

        output = await self.mock(mock_return_popen_stdout)
        self.assertEqual(expected, output)

    async def test_strange_symbols(self):
        """
        Basic test case where everything should work as expected

        """
        mock_return_popen_stdout = b"123123$$$1   []#';[]-=1   2=\n"

        expected = [data_io.StackDatum(123123,
                                       ("1   []#'", "[]-=1   2="))]

        output = await self.mock(mock_return_popen_stdout)
        self.assertEqual(output, expected)


class TCPTracerTest(asynctest.TestCase):
    time = 5

    @asynctest.patch('marple.collect.interface.ebpf.asyncio')
    @asynctest.patch('marple.collect.interface.ebpf.logger')
    @asynctest.patch('marple.collect.interface.ebpf.os')
    @asynctest.patch('marple.collect.interface.ebpf.TCPTracer._generate_dict')
    @asynctest.patch('marple.collect.interface.ebpf.TCPTracer._generate_events')
    async def test_collect_normal(self, gen_events_mock, gen_dict_mock, os_mock,
                                  log_mock, async_mock):
        """
        Test normal operation, when tcptracer outputs KeyboardInterrupt only

        """
        # Set up mocks
        create_mock = asynctest.CoroutineMock()
        wait_mock = asynctest.CoroutineMock()

        # Set up subprocess
        async_mock.create_subprocess_shell = create_mock

        pipe_mock = async_mock.subprocess.PIPE

        # Set up timeout stuff
        async_mock.wait = wait_mock
        output_mock = asyncio.Future()
        output_mock.set_result(
            (b'output', b'Traceback (most recent call last):\nstacktrace'
                        b'\nstacktrace etc.\nKeyboardInterrupt\n'))
        wait_mock.side_effect = [([None], [output_mock])]

        # Begin test
        collecter = ebpf.TCPTracer(self.time, None)
        await collecter.collect()

        # Run checks
        create_mock.assert_has_calls([
            asynctest.call(
                ebpf.BCC_TOOLS_PATH + 'tcptracer ' + '-tv',
                stdout=pipe_mock, stderr=pipe_mock, preexec_fn=os_mock.setsid
            ),
            asynctest.call().communicate()
        ])

        wait_mock.assert_called_once_with(
            [async_mock.ensure_future(
                create_mock.return_value.communicate.return_value)],
            timeout=self.time
        )

        os_mock.killpg.assert_called_once_with(create_mock.return_value.pid,
                                               ebpf.signal.SIGINT)

        log_mock.error.assert_not_called()

        gen_dict_mock.assert_called_once()
        gen_events_mock.assert_called_once()

    @asynctest.patch('marple.collect.interface.ebpf.asyncio')
    @asynctest.patch('marple.collect.interface.ebpf.logger')
    @asynctest.patch('marple.collect.interface.ebpf.os')
    @asynctest.patch('marple.collect.interface.ebpf.TCPTracer._generate_dict')
    @asynctest.patch('marple.collect.interface.ebpf.TCPTracer._generate_events')
    async def test_collect_error(self, gen_events_mock, gen_dict_mock, os_mock,
                                 log_mock, async_mock):
        """
        Test error operation, when tcptracer outputs an error

        """
        # Set up mocks
        create_mock = asynctest.CoroutineMock()
        wait_mock = asynctest.CoroutineMock()

        # Set up subprocess
        async_mock.create_subprocess_shell = create_mock

        pipe_mock = async_mock.subprocess.PIPE

        # Set up timeout stuff
        async_mock.wait = wait_mock
        output_mock = asyncio.Future()
        output_mock.set_result(
            (b'output', b'Traceback (most recent call last):\nstacktrace'
                        b'\nstacktrace etc.\nKeyboardInterrupt\nERROR'))
        wait_mock.side_effect = [([None], [output_mock])]

        # Begin test
        collecter = ebpf.TCPTracer(self.time, None)
        await collecter.collect()

        # Run checks
        create_mock.assert_has_calls([
            asynctest.call(
                ebpf.BCC_TOOLS_PATH + 'tcptracer ' + '-tv',
                stdout=pipe_mock, stderr=pipe_mock, preexec_fn=os_mock.setsid
            ),
            asynctest.call().communicate()
        ])

        wait_mock.assert_called_once_with(
            [async_mock.ensure_future(
                create_mock.return_value.communicate.return_value)],
            timeout=self.time
        )

        os_mock.killpg.assert_called_once_with(create_mock.return_value.pid,
                                               ebpf.signal.SIGINT)

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

    @asynctest.patch('marple.collect.interface.ebpf.output')
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
            asynctest.call(
                    text="IPC: Could not find destination port PID/comm. "
                         "Check log for details.",
                    description="Could not find destination port PID/comm: "
                                "Time: 1  Type: A  Source PID: 2  "
                                "Source comm: comm1  Source port : 3  "
                                "Dest port: 4  Net namespace: 5"
            ),
            asynctest.call(
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
            data_io.EventDatum(time=1, type='A',
                               specific_datum=(
                                    2, 'comm1', 3, 'pid1', 'test1', 4, 5)),
            data_io.EventDatum(time=6, type='B',
                               specific_datum=(
                                    7, 'comm2', 4, 'pid2', 'test2', 3, 5))
        ]
        self.assertEqual(expected, result)

    @asynctest.patch('marple.collect.interface.ebpf.output')
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
            data_io.EventDatum(time=1, type='A',
                               specific_datum=(
                                    2, 'comm1', 3, 'pid1', 'test1', 4, 5)),
        ]
        self.assertEqual(expected, result)

        expected_errors = [
            asynctest.call(
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