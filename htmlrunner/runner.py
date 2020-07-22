import platform
from datetime import datetime
import os
import time
import unittest
import threading

from collections import defaultdict

from logz import log
from jinja2 import Template

from htmlrunner.result import Result
from htmlrunner.loader import Loader
from htmlrunner.utils import isnotsuite, group_test_by_class


BASEDIR = os.path.dirname(os.path.abspath(__file__))


DEFAULT_REPORT_FILE = 'report.html'

DEFAULT_LOG_FILE = 'run.log'

DEFAULT_REPORT_TITLE = 'TEST REPORT BY HTMLRUNNER'

DEFAULT_TEMPLATE = 'default'


def run_suite_after(suite, result):  # todo
    suite._tearDownPreviousClass(None, result)
    suite._handleModuleTearDown(result)


def run_suite_before_case(suite, case, result):  # todo
    suite._tearDownPreviousClass(case, result)
    suite._handleModuleFixture(case, result)
    suite._handleClassSetUp(case, result)
    result._previousTestClass = case.__class__
    if (getattr(case.__class__, '_classSetupFailed', False) or getattr(result, '_moduleSetUpFailed', False)):
        return False
    return True


class Runner(object):
    def __init__(self,
                 threads=None,
                 timeout=None,
                 interval=None,
                 failfast=False,
                 ensure_sequence=True,
                 check_all=False,
                 **kwargs):
        self.threads = threads
        self.interval = interval
        self.reruns = False  # todo
        self.timeout = timeout   # 每个用例的执行时间
        self.failfast = failfast
        self.kwargs = kwargs
        self.ensure_sequence = ensure_sequence  # 确保运行顺序
        self.check_all = check_all  # todo

    def run_with_threads(self, case, result):
        assert self.threads and isinstance(self.threads, int) and self.threads > 0
        if self.timeout:
            assert isinstance(self.timeout, (float, int)) and self.timeout > 0

        threads = []
        for i in range(self.threads):
            threads.append(threading.Thread(target=case, args=(result,)))

        [t.start() for t in threads]

        [t.join(timeout=self.timeout) for t in threads]

    def run_test(self, test, result):
        """执行单个测试"""
        if self.threads and isinstance(self.threads, int):
            print(self.threads, self.timeout)
            self.run_with_threads(test, result)
        else:
            test(result)
        interval = self.interval
        print('interval', interval)
        if interval and isinstance(interval, (int, float)):
            time.sleep(interval)

    def run_suite(self, suite, result):
        """基础运行suite方法"""
        log.info('执行测试套件:', suite)
        topLevel = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = topLevel = True

        for index, test in enumerate(suite):
            if isnotsuite(test):
                setup_ok = run_suite_before_case(suite, test, result)
                if not setup_ok:
                    continue
            self.run_test(test, result)
            if suite._cleanup:
                suite._removeTestAtIndex(index)

        if topLevel:
            run_suite_after(suite, result)
            result._testRunEntered = False

        return result

    def run(self, suite, callback=None, interval=None):
        result = Result()
        result.failfast = self.failfast is True

        result.start_at = datetime.now()
        self.run_suite(suite, result)
        result.end_at = datetime.now()
        if callback:
            callback(result)
        return result


class HTMLRunner(Runner):
    def __init__(self, report_file=None, log_file=None,  output=None, # 报告文件, 日志文件, 自动创建路径
                 title=None, description=None, tester=None,   # 报告内容
                 template=None, lang=None,  # 模板及语言
                 verbosity=2, failfast=False,
                 threads=None, timeout=None,  # 运行选项
                 interval=None,
                 **kwargs):  # 额外信息
        self.verbosity = verbosity
        self.failfast = failfast
        self.interval = interval
        self.output = output
        self.report_file = datetime.now().strftime(report_file or DEFAULT_REPORT_FILE)
        self.log_file = log.file = datetime.now().strftime(log_file or DEFAULT_LOG_FILE)

        self.title = title or DEFAULT_REPORT_TITLE
        self.description = description
        self.tester = tester
        self.template = template or DEFAULT_TEMPLATE
        self.kwargs = kwargs
        super().__init__(threads, timeout, interval)

    def generate_report(self, result):
        template_path = os.path.join(BASEDIR, 'templates', '%s.html' % self.template)

        with open(template_path) as f:
            template_content = f.read()

        test_classes = result.sortByClass()
        # 报告配置信息
        report_config_info = {
            "title": self.title,
            "description": self.description,
            "tester": self.tester
        }
        # 结果统计
        result_stats_info = {
            "total": result.totol,
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
        # 环境信息
        env_info = result.get_env_info()
        context = {
            "result": result,
            "test_cases": result.result,
            "test_classes": test_classes,
        }
        [context.update(info) for info in (report_config_info,
                                           result_stats_info,
                                           env_info,
                                           self.kwargs)]  # 额外变量

        content = Template(template_content).render(context)
        if self.output:
            if not os.path.isdir(self.output):
                os.makedirs(self.output)  # todo try
        self.report_file = os.path.join(self.output, self.report_file)
        with open(self.report_file, "w") as f:
            f.write(content)

    def run(self, suite, callback=None, interval=None, debug=False):
        result = super().run(suite, callback=self.generate_report, interval=interval)
        return result


if __name__ == "__main__":
    pass