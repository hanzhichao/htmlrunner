import re
import unittest
from collections import defaultdict


TAG_PARTTEN = 'tag:(\w+)'

LEVEL_PARTTEN = 'level:(\d+)'

ORDER_PARTTEN = 'order:(\d+)'

GLOBAL_ORDER_PARTTEN = 'global_order:(\d+)'


def isnotsuite(test):
    """判断test是suite还是case"""
    try:
        iter(test)
    except TypeError:
        return True
    return False


def flatten_suite(suite):
    new_suite = unittest.TestSuite()

    def _collect(suite):
        for test in suite:
            if isnotsuite(test):
                new_suite.addTest(test)
            elif test.countTestCases() > 0:
                _collect(test)

    _collect(suite)
    return new_suite


def group_test_by_class(suite: unittest.TestSuite) -> unittest.TestSuite:
    suite = flatten_suite(suite)
    suite_dict = defaultdict(unittest.TestSuite)
    for test in suite:
        if isnotsuite:
            suite_dict[test.__class__].addTest(test)
    return unittest.TestSuite(suite_dict.values())


def get_case_tags(case) -> list:
    case_tags = []
    case_doc = case._testMethodDoc
    if case_doc and 'tag' in case_doc:
        pattern = re.compile(TAG_PARTTEN)
        case_tags = re.findall(pattern, case_doc)
    return case_tags


def get_case_level(case):
    case_doc = case._testMethodDoc
    case_level = -1  # todo 默认level
    if case_doc:
        pattern = re.compile(LEVEL_PARTTEN)
        levels = re.findall(pattern, case_doc)
        if levels:
            case_level = levels[0]
            try:
                case_level = int(case_level)
            except:
                raise ValueError(f'用例中level设置：{case_level} 应为整数格式')
    return case_level


def get_case_order(case):
    case_doc = case._testMethodDoc
    case_order = 100  # todo
    if case_doc:
        pattern = re.compile(ORDER_PARTTEN)
        orders = re.findall(pattern, case_doc)
        if orders:
            case_order = orders[0]
            try:
                case_order = int(case_order)
            except:
                raise ValueError(f'用例中order设置：{case_order} 应为整数格式')
    return case_order


def get_case_images(case):
    if hasattr(case, 'images'):
        images = case.images
        return images
    return []