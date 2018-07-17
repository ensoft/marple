import collect.test.util as util


class _BaseTest(util.BaseTest):
    """Base test class"""


# -----------------------------------------------------------------------------
# Tests
#

class StackTest(_BaseTest):
    """Class for testing data conversion of stack data"""
    def setUp(self):
        """Per-test set-up"""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down"""
        super().tearDown()

    def test_create(self):
        """Check that counter works"""
        # Stub out write
        # Example in check out
        # also tests datatypes implicitly for hashability


class EventTest(_BaseTest):
    """Class for testing data conversion of event data"""
    def setUp(self):
        """Per-test set-up"""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down"""
        super().tearDown()

    def test_create(self):
        """Check that the output format is correct"""
        pass
