# -------------------------------------------------------------
# test_smem.py - tests for interactions with smem
# September 2018 - Andrei Diaconu
# -------------------------------------------------------------

""" Test the smem module. """

import asynctest

from marple.collect.interface import smem
from marple.common import data_io


class SmemTest(asynctest.TestCase):
    """ Test memtime data collection. """
    time = 2
    async_mock, log_mock, pipe_mock = None, None, None

    def run(self, result=None):
        """ Override run() to set up mocks """
        # !!! Dangerous to mock things here since they might be used in
        # asynctest (for example time.monotonic was used in there, and it
        # called it ouside the smem module, causing StopIteration errors in
        # the side_effect iterable)
        with asynctest.patch('marple.collect.interface.smem.asyncio') as \
                async_mock, \
             asynctest.patch('marple.collect.interface.smem.logger') as \
                log_mock:
            self.async_mock = async_mock

            # Mock subprocess creator
            create_mock = asynctest.CoroutineMock()
            async_mock.create_subprocess_shell = create_mock
            async_mock.create_subprocess_shell.return_value.returncode = 0

            async_mock.sleep = asynctest.CoroutineMock()

            # Mock communicate()
            comm_mock = asynctest.CoroutineMock()
            time0 = (b"Name                          PSS\n"
                     b"A                            1024\n"
                     b"B                            1024\n"
                     b"C                            1024\n",
                     b"no_err1")
            time1 = (b"Name                          PSS\n"
                     b"D                            2048\n"
                     b"E                            2048\n"
                     b"F                            2048\n",
                     b"no_err2")
            # We use two sets of data, that represent data collected by
            # smem at different times
            comm_mock.side_effect = [time0, time1]
            create_mock.return_value.communicate = comm_mock

            self.log_mock = log_mock
            self.pipe_mock = async_mock.subprocess.PIPE

            super().run(result)

    @asynctest.patch('marple.collect.interface.smem.time.monotonic')
    @asynctest.patch('marple.common.util.platform.release')
    async def test_normal(self, release_mock, mono_patch):
        mono_patch.side_effect = [0, 1, 2]  # so we get exactly 2 collections
        release_mock.return_value = "100.0.0"  # so we ignore the kernel check

        collecter = smem.MemoryGraph(self.time)
        data = await collecter.collect()
        datapoints = list(data.datum_generator)
        self.async_mock.create_subprocess_shell.assert_has_calls([
            asynctest.call(
                "smem -c \"name pss\"",
                stdout=self.pipe_mock, stderr=self.pipe_mock),
            asynctest.call().communicate(),
            asynctest.call(
                "smem -c \"name pss\"",
                stdout=self.pipe_mock, stderr=self.pipe_mock),
            asynctest.call().communicate(),
        ])

        # self.log_mock.error.assert_called_once_with('test_err')
        expected = [data_io.PointDatum(x=0.0, y=1.0, info='C'),
                    data_io.PointDatum(x=0.0, y=1.0, info='B'),
                    data_io.PointDatum(x=0.0, y=1.0, info='A'),
                    data_io.PointDatum(x=1.0, y=2.0, info='F'),
                    data_io.PointDatum(x=1.0, y=2.0, info='E'),
                    data_io.PointDatum(x=1.0, y=2.0, info='D')]
        self.assertEqual(expected, datapoints)
