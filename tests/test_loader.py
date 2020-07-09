import unittest
from htmlrunner.loader import Loader, group_test_by_class
from htmlrunner.runner import Runner, HTMLRunner

# suite = unittest.defaultTestLoader.discover('tests')
# for test in suite:
#     print(test)
#
# suite = group_test_by_class(suite)
# print('-'*30)
# for test in suite:
#     print(test)

#
class TestA(unittest.TestCase):
    def test_a(self):
        """order:2"""
        pass

    def test_b(self):
        self.images = ['hello']
        pass

    def test_c(self):
        """order:1"""
        pass

loader = Loader(suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestA))
runner = Runner()
runner.run(loader.suite)