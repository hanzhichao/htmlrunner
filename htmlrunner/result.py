import sys
import io
import unittest
from datetime import datetime
from collections import defaultdict
from itertools import groupby
import inspect
import importlib

from logz import log

from htmlrunner.loader import flatten_suite


class OutputRedirector(object):
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
        self.result[test.id()]['end_at'] = test.end_at = datetime.now()
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
        test.output = output = self.complete_output()
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

        tags, = getattr(test, 'tags') if hasattr(test, 'tags') else [],
        level = test.level if hasattr(test, 'level') else 2

        start_at = test.start_at if hasattr(test, 'start_at') else None
        end_at = test.end_at if hasattr(test, 'end_at') else None  # 注册时未结束无end_at
        test.duration = duration = (test.end_at - test.start_at) if start_at and end_at else 0
        test.status = status

        try:
            code = inspect.getsource(test_method)
        except Exception as ex:
            log.exception(ex)
            code = ''

        if test.id() not in self.result:
            item = dict(obj=test,
                        sn=self.sn,
                        name=test_method_name,
                        full_name=str(test),
                        full_path=test.id(),
                        doc=test_method_doc,
                        code=code,
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
                        tags=tags,
                        level=level
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
                pass_num=len(list(filter(lambda x: x['status' ]=="PASS", test_cases))),
                error_num=len(list(filter(lambda x: x['status' ]=="ERROR", test_cases))),
                fail_num=len(list(filter(lambda x: x['status' ]=="FAIL", test_cases))),
                skipped_num=len(list(filter(lambda x: x['status' ]=="SKIPPED", test_cases))),
                xfail_num=len(list(filter(lambda x: x['status' ]=="XFAIL", test_cases))),
                xpass_num=len(list(filter(lambda x: x['status' ]=="XPASS", test_cases)))
            )
        test_classes = list(data.values())
        return test_classes

    def addTimeout(self, err, test):
        self.timeouts.append(test)

    def handle_load_error(self, test, err):
        err_desc = test.id().replace('(' ,'').replace(')' ,'')
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
        err_desc = test.id().replace('(' ,'').replace(')' ,'')
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
                # self.register(unrun_test, '%s_ERROR' % function_name, '')
                self.register(unrun_test, 'ERROR')

    def handle_class_setup_teardown_error(self, test, err):
        err_desc = test.id().replace('(' ,'').replace(')' ,'')
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
            err_desc = test.id().replace('(' ,'').replace(')' ,'')
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