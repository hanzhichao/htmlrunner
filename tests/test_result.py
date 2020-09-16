import sys
sys.path.insert(0, '/Users/superhin/项目/htmlrunner')
from htmlrunner.result import TestResult


import unittest
import time


class MyTestCase(unittest.TestCase):
    def test_something(self):
        """测试1
        level:3
        """
        self.level=1
        print('test_something')
        print(1/0)

        # time.sleep(1)
        self.assertEqual(True, False)

    def test_something2(self):
        # time.sleep(1)
        self.tags=['abc']
        print('test_something2')

    def test_something3(self):
        """测试3
        tag:smoke
        tag:abc
        tag:bcd
        """
        # time.sleep(1)
        print('test_something3')


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MyTestCase)
    runner = unittest.TextTestRunner(verbosity=2, tb_locals=True, buffer=True, resultclass=TestResult)
    result = runner.run(suite)
    from pprint import pprint

    pprint(result.summary)