"""hello"""

import sys
sys.path.insert(0, '/Users/superhin/项目/htmlrunner')
from htmlrunner.result import TestResult


import unittest
import time


class MyTestCase(unittest.TestCase):
    """测试MytestCase"""
    def test_something(self):
        """测试1
        level:3
        """
        a = 1
        b = 2
        self.level=1
        print('test_something')
        print(1/0)

        # time.sleep(1)


    def test_something2(self):
        # time.sleep(1)
        self.tags=['abc']
        print('test_something2')
        self.assertEqual(True, False, msg='True 不等于 False')

    def test_something3(self):
        """测试3
        tag:smoke
        tag:abc
        tag:bcd
        """
        # time.sleep(1)
        print('test_something3')
        assert 1==0, '1不等于0呀'


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MyTestCase)
    runner = unittest.TextTestRunner(verbosity=2, tb_locals=True, buffer=True, resultclass=TestResult)
    result = runner.run(suite)
    from pprint import pprint

    # pprint(result.data_by_class)
    pprint(result.data)