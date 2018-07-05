import unittest
import os
import collect.interface.perf as perf

TEST_DATA = os.path.dirname(os.path.abspath(__file__))+"/perf.data"


class PerfTest(unittest.TestCase):
    """
    Unit test of the interface.perf module.

    Warning: test uses path name of the test module via __file__
    which does not work if it is called using exec or execfile.

    """
    def test_sched_data_pos(self):
        """positive test: use provided perf.data file"""
        perf.get_sched_data()
        self.assertRaises(FileExistsError)

    def test_sched_data_neg(self):
        """negative test: no perf.data file available"""
        pass

    def tearDown(self):
        if os.path.exists(TEST_DATA):
            pass
            # os.remove(TEST_DATA)


if __name__ == "__main__":
    unittest.main()
