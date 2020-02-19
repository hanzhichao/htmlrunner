import unittest
import logging


class TestDemo22(unittest.TestCase):
    def test_success(self):
        print('success')

    def test_fail(self):
        logging.info('fail')
        assert 0

    def test_error(self):
        logging.error('error')
        open('abc.txt')

    @unittest.skipIf(True, '原因')
    def test_skip(self):
        print('skip')