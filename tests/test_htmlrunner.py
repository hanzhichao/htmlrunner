import os
import sys
sys.path.append('/Users/apple/Documents/Projects/Self/PyPi/htmlrunner')
import unittest
from htmlrunner import Runner,  HTMLRunner
from htmlrunner.loader import group_suites_by_class, flatten_suite
from htmlrunner.result import Result

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
testpath = os.path.join(basedir, 'tests', 'data')
suite = unittest.defaultTestLoader.discover(testpath)
result = Result()
runner = Runner()

# test_error (demo2.demo22.test_demo22.TestDemo22) <class 'demo2.demo22.test_demo22.TestDemo22'> (<class 'FileNotFoundError'>, FileNotFoundError(2, 'No such file or directory'), <traceback object at 0x110029208>) <class 'tuple'>
# setUpModule (demo2.test_demo2) <class 'unittest.suite._ErrorHolder'> (<class 'NameError'>, NameError("name 'sleep' is not defined",), <traceback object at 0x110002088>) <class 'tuple'>
# tearDownModule (demo2.test_demo2) <class 'unittest.suite._ErrorHolder'> (<class 'NameError'>, NameError("name 'sleep' is not defined",), <traceback object at 0x100eed088>) <class 'tuple'>
# setUpClass (demo2.test_demo2.TestDemo2) <class 'unittest.suite._ErrorHolder'> (<class 'NameError'>, NameError("name 'sleep' is not defined",), <traceback object at 0x10d0eb908>) <class 'tuple'>

def test_result_setup_module_error():
    suite = unittest.defaultTestLoader.discover(testpath)
    runner.run_suite(suite, result)
    print(result)


def test_flatten_suite():
    suite = unittest.defaultTestLoader.discover(testpath)
    suite = flatten_suite(suite)
    print(suite.countTestCases())
    assert suite.countTestCases() == 16

def test_collect_only():
    suite = unittest.defaultTestLoader.discover(testpath)
    runner.collect_only(suite)

def test_run_suite():
    suite = unittest.defaultTestLoader.discover(testpath)
    result = unittest.result.TestResult()
    runner.run_suite(suite, result)
    print(result)

def test_run_suite_in_thread_poll():
    suite = unittest.defaultTestLoader.discover(testpath)
    result = unittest.result.TestResult()
    runner.run_suite_in_thread_poll(suite, result)
    print(result)

def test_group_suites_by_class():
    suite = unittest.defaultTestLoader.discover(testpath)
    suite_list = group_suites_by_class(suite)
    assert 3 == len(suite_list)


def test_timeout():
    suite = unittest.defaultTestLoader.discover(testpath)
    runner.run_with_timeout(suite, result, 3)
    
def test_with_default_template():
    suite = unittest.defaultTestLoader.discover(testpath)
    HTMLRunner(output="report.html",
               title="测试报告",
               description="测试报告描述", tester='Hzc').run(suite)

def test_with_htmltestreportcn_template():
    suite = unittest.defaultTestLoader.discover(testpath)
    HTMLRunner(output="report_httptestreportcn.html",
               title="测试报告",
               description="测试报告描述", tester='Hzc',template='htmltestreportcn').run(suite)


def test_with_pytest_html_template():
    suite = unittest.defaultTestLoader.discover(testpath)
    HTMLRunner(output="report_pytest_html.html",
               title="测试报告",
               description="测试报告描述", tester='Hzc',template='pytest_html').run(suite)


if __name__ == "__main__":
    test_with_default_template()