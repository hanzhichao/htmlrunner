import unittest
import sys
sys.path.append('/Users/superhin/项目/htmlrunner')
from htmlrunner.decorators import tag, level



class TestA(unittest.TestCase):

    @tag(['smoke', 'abc', 'api'])
    def test_a(self):
        pass

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestA)
    print(suite)
    for case in suite:
        test_method = getattr(case, case._testMethodName)
        print(case, test_method.tags)
