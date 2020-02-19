import unittest
import logging
import ddt

data = [1, 2, 3, 4]

@ddt.ddt
class TestDemo1(unittest.TestCase):

    @ddt.data(*data)
    def test_success(self, value):
        print('success with %s' %value)

    def test_fail(self):
        logging.info('fail')
        print('fail')
        assert 0

    def test_error(self):
        print('error')
        logging.error('error')
        open('abc.txt')

    @unittest.skipIf(True, '原因')
    def test_skip(self):
        print('skip')