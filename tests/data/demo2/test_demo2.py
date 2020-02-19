import unittest
import logging
import time
from random import randint

# sleep(1)
def a():
    time.sleep(1)


def setUpModule():
    # sleep(randint(1,3))
    # a()
    print('setup module')


def tearDownModule():
    sleep(randint(1,3))
    print('teardown module')


class TestDemo2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sleep(1)
        print('setup class')

    @classmethod
    def tearDownClass(cls):
        print('teardown class')

    def setUp(self):
        print('setup')

    def tearDown(self):
        print('teardown')


    def test_success(self):
        # print('hello', vars())
        # print(self.__dict__)
        # print(self.testMethod)
        print(self, type(self))
        self.tags = ['hello']
        print('hello', self.tags)
        print('success')

    def test_timeout(self):
        print('timeout')
        print(self.tags)
        time.sleep(3)

    def test_fail(self):
        logging.info('fail')
        assert 0

    def test_error(self):
        logging.error('error')
        open('abc.txt')

    @unittest.skipIf(True, '原因')
    def test_skip(self):
        print('skip')
