import time
import platform
from datetime import datetime
import os
import unittest
from jinja2 import Template
from collections import defaultdict
from itertools import groupby
import sys
import io
from unittest.suite import _isnotsuite
import pickle
import time
import signal
import inspect
import importlib
from concurrent.futures import ThreadPoolExecutor

class TimeoutError(Exception):
    def __init__(self, msg):
        super(TimeoutError, self).__init__()
        self.msg = msg

def set_timeout(interval, callback):
    def decorator(func):
        def handler(signum, frame):
            raise TimeoutError("run func timeout")
        def wrapper(*args, **kwargs):
            try:
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(interval)       # interval秒后向进程发送SIGALRM信号
                result = func(*args, **kwargs)
                signal.alarm(0)              # 函数在规定时间执行完后关闭alarm闹钟
                return result
            except TimeoutError as e:
                callback(func, e)
        return wrapper
    return decorator

def run_suite_after(suite, result):
    suite._tearDownPreviousClass(None, result)
    suite._handleModuleTearDown(result)

def run_suite_before_case(suite, case, result):
    suite._tearDownPreviousClass(case, result)
    suite._handleModuleFixture(case, result)
    suite._handleClassSetUp(case, result)
    result._previousTestClass = case.__class__
    if (getattr(case.__class__, '_classSetupFailed', False) or getattr(result, '_moduleSetUpFailed', False)):
        return False
    return True

def flatten_suite(suite):
    new_suite = unittest.TestSuite()
    def _collect(suite):
        for test in suite:
            if _isnotsuite(test):
                new_suite.addTest(test)
            elif test.countTestCases() > 0:
                _collect(test)
    _collect(suite)
    return new_suite


def group_suites_by_class(suite):
    suite = flatten_suite(suite)
    suite_dict = defaultdict(unittest.TestSuite)
    for test in suite:
        if _isnotsuite:
            suite_dict[test.__class__].addTest(test)
    suite_list = list(suite_dict.values())
    return suite_list

class Loader(unittest.TestLoader):

    # def discover(self, testspath='.', pattern="*.py"):
    #     return unittest.defaultTestLoader.discover(testspath, pattern)

    
    def load_tests_by_config(self, testlist_file):  # test_list_file配置在config/config.py中
        with open(testlist_file) as f:
            testlist = f.readlines()

        testlist = [i.strip() for i in testlist if not i.startswith("#")]   # 去掉每行结尾的"/n"和 #号开头的行

        suite = unittest.TestSuite() 
        all_cases = collect()  # 所有用例
        for case in all_cases:  # 从所有用例中匹配用例方法名
            if case._testMethodName in testlist:
                suite.addTest(case)
        return suite

    def load_tests_by_tag(self, expr):
        suite = unittest.TestSuite()
        for case in collect():
            if case._testMethodDoc and tag in case._testMethodDoc:  # 如果用例方法存在docstring,并且docstring中包含本标签
                suite.addTest(case)
        return suite

    
    def load_tests_by_level(self, expr):
        pass

    def load_last_fails(self):
        pass
    
class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()

stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


class Result(unittest.TestResult):
    def __init__(self, verbosity=1):
        super().__init__(verbosity=verbosity)
        self.verbosity = verbosity
        self.timeouts = []
        self.success = []
        self.timeouts = []
        self.result = {}
        self.test_class = defaultdict(list)
        self.sn = 1
        self.stdout_bak = None
        self.stderr_bak = None
    
    def capture_output(self):
        # 重定向sys.out和sys.err
        self.output = io.StringIO()
        stdout_redirector.fp = self.output
        stderr_redirector.fp = self.output
        self.stdout_bak = sys.stdout
        self.stderr_bak = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def complete_output(self):
        if self.stdout_bak:
            sys.stdout = self.stdout_bak
            sys.stderr = self.stderr_bak
            self.stdout_bak = None
            self.stderr_bak = None
        return self.output.getvalue()

    def startTest(self, test):
        self.capture_output()
        test.start_at = datetime.now()
        super().startTest(test)
        
    
    def stopTest(self, test):
        test.end_at = datetime.now()
        self.complete_output()


    def update_test(self, test, status, exec_info='', setup_status=None, teardown_status=None, error_code=None):
        output = self.complete_output()
        sys.stdout.write(output)
        last_output = self.result[test.id()].get(output, '')
        last_exec_info = self.result[test.id()].get(output, '')
        self.result[test.id()].update(
            {
                'output': '\n'.join([last_output, output]),
                'exec_info': '\n'.join([last_exec_info, exec_info]),
            }
        )

    def register(self, test, status, exec_info='', setup_status=None, teardown_status=None, error_code=None):
        output = self.complete_output()
        sys.stdout.write(output)

        test_module_name = test.__module__
        test_class_name = test.__class__.__name__
        test_class_doc = test.__class__.__doc__
        test_method_name = test._testMethodName
        test_method_doc = test._testMethodDoc

        if test_module_name == '__main__':
            test_module_name = ''
        else:
            test_class_name = '%s.%s' % (test_module_name, test_class_name)

        test_method = getattr(test.__class__, test_method_name)  # TODO  模块中代码块的失败

        tags = test.tags if hasattr(test, 'tags') else [],
        level = test.level if hasattr(test, 'level') else 2

        start_at=test.start_at if hasattr(test, 'start_at') else None
        end_at=test.end_at if hasattr(test, 'end_at') else None
        duration=(test.end_at - test.start_at) if start_at and end_at else 0

        if test.id() not in self.result:
            item = dict(obj=test, 
                sn = self.sn,
                name=test_method_name,
                full_name=str(test),
                full_path=test.id(),
                doc=test_method_doc,
                code=inspect.getsource(test_method),
                status=status,
                setup_status=setup_status,
                teardown_status=teardown_status,
                test_class=test_class_name,
                test_class_doc=test_class_doc,
                test_module=test_module_name,
                start_at=start_at,
                end_at=end_at,
                duration=duration,
                exec_info=exec_info,
                output=output,
                tags = tags,
                level = level
                )
            self.result[test.id()] = item
            self.sn += 1
        else:
            self.update_test(test, status, exec_info=exec_info, 
            setup_status=setup_status, 
            teardown_status=teardown_status, 
            error_code=error_code)
            
    def sortByClass(self):
        sorted_result = sorted(list(self.result.values()), key=lambda x: x['test_class'])
        data = defaultdict(dict)
        for name, group in groupby(sorted_result, key=lambda x: x['test_class']):
            test_cases = list(group)
            data[name] = dict(
                name=name,
                test_cases=test_cases,
                total=len(test_cases),
                pass_num=len(list(filter(lambda x: x['status']=="PASS", test_cases))),
                error_num=len(list(filter(lambda x: x['status']=="ERROR", test_cases))),
                fail_num=len(list(filter(lambda x: x['status']=="FAIL", test_cases))),
                skipped_num=len(list(filter(lambda x: x['status']=="SKIPPED", test_cases))),
                xfail_num=len(list(filter(lambda x: x['status']=="XFAIL", test_cases))),
                xpass_num=len(list(filter(lambda x: x['status']=="XPASS", test_cases)))
            )
            test_classes = list(data.values())
        return test_classes

    def addTimeout(self, err, test):
        self.timeouts.append(test)


    def handle_load_error(self, test, err):
        err_desc = test.id().replace('(','').replace(')','')
        function_name, path = err_desc.split()

        path = function_name
        module = importlib.import_module(path)
        function = None
        tests = unittest.defaultTestLoader.loadTestsFromModule(module) 
            
        if tests:
            tests = flatten_suite(tests)
            for unrun_test in tests:
                exec_info = self._exc_info_to_string(err, test)
                self.errors.append((unrun_test, ))
                self.register(unrun_test, 'LOAD_ERRROR', '')
        

    def handel_module_setup_teardown_error(self, test, err):
        err_desc = test.id().replace('(','').replace(')','')
        function_name, path = err_desc.split()

        module = importlib.import_module(path)
        function = getattr(module, function_name)
        tests = unittest.defaultTestLoader.loadTestsFromModule(module)
        error_code = inspect.getsource(function)  
            
        if tests:
            tests = flatten_suite(tests)
            for unrun_test in tests:
                exec_info = self._exc_info_to_string(err, test)
                self.errors.append((unrun_test, ))
                self.register(unrun_test, '%s_ERROR' % function_name, '')

    def handle_class_setup_teardown_error(self, test, err):
        err_desc = test.id().replace('(','').replace(')','')
        function_name, path = err_desc.split()
        full_path = path.split('.')
        module_path = '.'.join(full_path[:-1])
        class_name = full_path[-1]
        module = __import__(module_path, globals(), locals(), [class_name])
        test_class = getattr(module, class_name)
        function = getattr(test_class, function_name)
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(test_class)

        if tests:
            tests = flatten_suite(tests)
            for unrun_test in tests:
                exec_info = self._exc_info_to_string(err, test)
                self.errors.append((unrun_test, ))
                self.register(unrun_test, '%s_ERROR' % function_name, '')

    
    def addError(self, test, err):   # 模块或类级Excepition时 result.addError(error, sys.exc_info())
        if isinstance(test, unittest.TestCase):
            self.errors.append((test, self._exc_info_to_string(err, test)))
            self.register(test, 'ERROR', self._exc_info_to_string(err, test))

        elif isinstance(test, unittest.loader._FailedTest):
            self.handle_load_error(test, err)
        else:
            err_desc = test.id().replace('(','').replace(')','')
            function_name, path = err_desc.split()
            if function_name in ['setUpModule', 'tearDownModule']:
                self.handel_module_setup_teardown_error(test, err)
            elif function_name in ['setUpClass', 'tearDownClass']:
                self.handle_class_setup_teardown_error(test, err)
            else:
                print('不支持处理该错误 %s' %function_name)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.register(test, 'FAIL', self._exc_info_to_string(err, test))

    def addSuccess(self, test):
        self.success.append(test)
        self.register(test, 'PASS')

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.register(test, 'SKIPPED', reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.register(test, 'XFAIL', self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.register(test, 'XPASS', 'UnexpectedSuccess')


class Runner(object):
    def collect_only(self, suite):
        t0 = time.time()
        i = 0
        suite = flatten_suite(suite)
        print("Collect {} tests is {:.3f}s".format(suite.countTestCases(),time.time()-t0))
        print("-"*50)
        for case in suite:
            if _isnotsuite(case):
                i += 1
                print("{}.{}".format(i, str(case)))
        print("-"*50)
        
    def run_suite(self, suite, result, run_func=None, interval=None):
        topLevel = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = topLevel = True

        for index, test in enumerate(suite):
            if _isnotsuite(test):
                setup_ok = run_suite_before_case(suite, test, result)
                if not setup_ok:
                    continue
            
            run_func(test, result) if run_func else test(result)  # 可能是suite 可能有异常
            time.sleep(interval) if interval else None

            if suite._cleanup:
                suite._removeTestAtIndex(index)

        if topLevel:
            run_suite_after(suite, result)
            result._testRunEntered = False
        
        return result

    def run_suite_by_class(self, suite, result, run_func=None, interval=None):
        suite_list = group_tests_by_class()
        for suite in suite_list:
            self.run_suite(suite, result, run_func=run_func, interval=interval)


    def run_suite_in_thread_poll(self, suite, result, thread_num=3, interval=None):
        poll = ThreadPoolExecutor(max_workers=thread_num)
        self.run_suite(suite, result, 
                       run_func=lambda case, result: poll.submit(case, result), 
                       interval=interval)

    def run_with_timeout(self, test, result, timeout):
        print(test, result, timeout)
        set_timeout(timeout, result.addTimeout)(test)(result)

    def run(self, suite, callback=None):
        result = Result()
        result.start_at = datetime.now()
        self.run_suite(suite, result)
        result.end_at = datetime.now()
        if callback:
            callback(result)
        return result

class HTMLRunner(Runner):
    def __init__(self, output, title="Test Report", description="", tester="",template='simple', **kwargs):
        self.file = datetime.now().strftime(output)
        self.title = title
        self.description = description
        self.tester = tester
        self.template = template
        self.kwargs = kwargs
        self.timeout = 10

    def generate_report(self, result):
        basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(basedir, 'templates', '%s.html' % self.template)

        with open(template_path) as f:
            template_content = f.read()
        
        test_classess = result.sortByClass()
        
        report_config_info = { 
            "title": self.title,
            "description": self.description,
            "tester": self.tester
            }
        result_stats_info = {
            "total": len(result.result),
            "run_num": result.testsRun,
            "pass_num": len(result.success),
            "fail_num": len(result.failures),
            "skipped_num": len(result.skipped),
            "error_num": len(result.errors),
            "xfail_num": len(result.expectedFailures),
            "xpass_num": len(result.unexpectedSuccesses),
            "rerun_num": 0,
            "start_at": result.start_at,
            "end_at": result.end_at,
            "duration": result.end_at - result.start_at,
        }
        env_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "python_version": platform.python_version(),
            "env": dict(os.environ),
        }
        context = {
            "result": result,
            "test_cases": result.result,
            "test_classes": test_classess,
        }
        [context.update(info) for info in (report_config_info, 
                                           result_stats_info, 
                                           env_info, 
                                           self.kwargs)]
        
        content = Template(template_content).render(context)
        with open(self.file, "w") as f:
            f.write(content)

    def run(self, suite):
        result = super().run(suite, callback=self.generate_report)
        return result


if __name__ == "__main__":

    pass