import unittest
import os
import time

from htmlrunner.utils import isnotsuite, flatten_suite, group_test_by_class, get_case_level, get_case_order, get_case_tags


class Loader(object):  # suite factory
    def __init__(self, testspath='.', pattern='test*.py', suite=None):
        self._loader = unittest.defaultTestLoader
        self._suite = suite
        self._testspath = testspath
        self._pattern = pattern

    @property
    def suite(self):
        """discover得到的原始suite"""
        if self._suite:
            assert isinstance(self._suite, unittest.TestSuite)
            return self._suite
        return self._loader.discover(self._testspath, self._pattern)

    @property  # todo 缓存
    def fsuite(self):
        """flatten后的suite,所有用例在同一层"""
        return flatten_suite(self.suite)

    @property
    def gsuite(self):
        """按测试类整理,每个测试类是一个单独的suite"""
        return group_test_by_class(self.suite)  # todo 直接使用self.fsuite

    @property
    def osuite(self):
        """按order整理顺序"""
        return unittest.TestSuite(
                [unittest.TestSuite(
                    sorted(suite, key=lambda case: get_case_order(case))
                )
                 for suite in self.gsuite])

    def collect_only(self, suite: unittest.TestSuite) -> None:
        t0 = time.time()
        i = 0
        print("Collect {} tests is {:.3f}s".format(suite.countTestCases(), time.time() - t0))
        print("-" * 50)
        for case in self.fsuite:
            if isnotsuite(case):  # todo remove
                i += 1
                print("{}.{}".format(i, str(case)))
        print("-" * 50)

    def collect_by_list(self, testlist_file: str) -> unittest.TestSuite:  # todo 直接load
        """通过配置文件筹集用例"""
        assert isinstance(testlist_file, str)
        assert os.path.isfile(testlist_file)

        with open(testlist_file) as f:
            testlist = f.readlines()

        testlist = set([i.strip() for i in testlist if not i.startswith("#")])
        suite = unittest.TestSuite()
        for case in self.fsuite:
            if case._testMethodName in testlist:
                suite.addTest(case)
        return suite

    def collect_by_dirs(self, dirs: list, pattern='test*.py') -> unittest.TestSuite:
        suites = []
        for dir in dirs:
            suite = self._loader.discover(start_dir=dir, pattern=pattern)
            suites.append(suite)
        return unittest.TestSuite(suites)

    def collect_by_tags(self, tags: list) -> unittest.TestSuite:  # todo 支持自定义suite
        assert isinstance(tags, list)
        new_suite = unittest.TestSuite()
        for case in self.fsuite:
            case_tags = get_case_tags(case)
            for tag in tags:
                if tag in case_tags:
                    new_suite.addTest(case)
                    break
        return new_suite

    def collect_by_level(self, level: int) -> unittest.TestSuite:
        """收集小于等于指定level的用例"""
        assert isinstance(level, int)
        new_suite = unittest.TestSuite()
        for case in self.fsuite:
            case_level = get_case_level(case)
            if 0 <= case_level <= level:  # 如果用例实际level <= 目标level，则运行
                new_suite.addTest(case)
        return new_suite

