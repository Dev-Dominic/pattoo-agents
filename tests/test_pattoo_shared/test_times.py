#!/usr/bin/env python3
"""Test the times module."""

# Standard imports
import unittest
import os
import sys

# Try to create a working PYTHONPATH
EXEC_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ROOT_DIRECTORY = os.path.abspath(os.path.join(
    os.path.abspath(os.path.join(EXEC_DIRECTORY, os.pardir)), os.pardir))
if EXEC_DIRECTORY.endswith('/pattoo-agents/tests/test_pattoo_shared') is True:
    sys.path.append(ROOT_DIRECTORY)
else:
    print('''\
This script is not installed in the "pattoo-agents/tests/test_pattoo_shared" \
directory. Please fix.''')
    sys.exit(2)

# Pattoo imports
from pattoo_shared import times
from tests.dev import unittest_setup


class TestBasicFunctions(unittest.TestCase):
    """Checks all functions and methods."""

    #########################################################################
    # General object setup
    #########################################################################
    def test_validate_timestamp(self):
        """Testing function validate_timestamp."""
        # Initialize key variables
        result = times.validate_timestamp(300, 300)
        self.assertEqual(result, True)
        result = times.validate_timestamp(400, 300)
        self.assertEqual(result, False)
        result = times.validate_timestamp(500, 300)
        self.assertEqual(result, False)
        result = times.validate_timestamp(500, '300')
        self.assertEqual(result, False)
        result = times.validate_timestamp('500', 300)
        self.assertEqual(result, False)
        result = times.validate_timestamp(500, 0)
        self.assertEqual(result, False)

    def test_normalized_timestamp(self):
        """Testing function normalized_timestamp."""
        # Initialize key variables
        polling_interval = 300

        timestamp = 31
        result = times.normalized_timestamp(
            polling_interval, timestamp=timestamp)
        self.assertEqual(result, (0, polling_interval))

        timestamp = 301
        result = times.normalized_timestamp(
            polling_interval, timestamp=timestamp)
        self.assertEqual(result, (300, polling_interval))

        timestamp = 900
        result = times.normalized_timestamp(
            polling_interval, timestamp=timestamp)
        self.assertEqual(result, (900, polling_interval))

        timestamp = 1000
        result = times.normalized_timestamp(
            polling_interval, timestamp=timestamp)
        self.assertEqual(result, (900, polling_interval))

        # Initialize key variables
        polling_interval = 30

        timestamp = 31
        result = times.normalized_timestamp(
            polling_interval, timestamp=timestamp)
        self.assertEqual(result, (30, polling_interval))

        timestamp = 301
        result = times.normalized_timestamp(
            polling_interval, timestamp=timestamp)
        self.assertEqual(result, (300, polling_interval))

        timestamp = 900
        result = times.normalized_timestamp(
            polling_interval, timestamp=timestamp)
        self.assertEqual(result, (900, polling_interval))

        timestamp = 1000
        result = times.normalized_timestamp(
            polling_interval, timestamp=timestamp)
        self.assertEqual(result, (990, polling_interval))


if __name__ == '__main__':
    # Make sure the environment is OK to run unittests
    unittest_setup.ready()

    # Do the unit test
    unittest.main()