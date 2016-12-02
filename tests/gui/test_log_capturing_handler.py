import unittest
import logging
from odk_tools.gui.log_capturing_handler import CapturingHandler


class TestCapturingHandler(unittest.TestCase):
    """Tests for the CapturingHandler class."""

    def test_capture_handler_output(self):
        """Should return list of log messages."""
        test_logger = logging.getLogger("my_test_logger")
        test_logger.setLevel("INFO")
        capture = CapturingHandler(logger=test_logger)
        messages = ["first message", "this is a second message"]
        test_logger.warning(messages[0])
        test_logger.info(messages[1])
        test_logger.removeHandler(hdlr=capture)
        self.assertEqual(capture.watcher.output, messages)