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
    # time.sleep(randint(1,3))
    print('teardown module')


class TestDemo2(unittest.TestCase):
    """测试Demo2"""
    @classmethod
    def setUpClass(cls):
        # time.sleep(1)
        print('setup class')

    @classmethod
    def tearDownClass(cls):
        print('teardown class')

    def setUp(self):
        print('setup')

    def tearDown(self):
        print('teardown')


    def test_success(self):
        """测试成功"""
        # print('hello', vars())
        # print(self.__dict__)
        # print(self.testMethod)
        print(self, type(self))
        self.tags = ['hello']
        self.images = ['/Users/superhin/Downloads/beida.jpeg']
        print('hello', self.tags)
        print('success')

    def test_timeout(self):
        """测试超时"""
        print('timeout')
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
