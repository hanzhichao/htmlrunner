import platform
from datetime import datetime
import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.suite import _isnotsuite

from logz import log
from jinja2 import Template

from htmlrunner.loader import flatten_suite, group_suites_by_class
from htmlrunner.result import Result
from htmlrunner.exceptions import set_timeout

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_REPORT_FILE = 'report.html'
DEFAULT_LOG_FILE = 'run.log'
DEFAULT_REPORT_TITLE = 'TEST REPORT BY HTMLRUNNER'
DEFAULT_TEMPLATE = 'all'


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


class Runner(object):
    def __init__(self, threads=None, timeout=None, by_class=False, **kwargs):
        self.threads = threads
        self.timeout = timeout
        self.by_class = by_class
        self.kwargs = kwargs

    def collect_only(self, suite):
        t0 = time.time()
        i = 0
        suite = flatten_suite(suite)
        print("Collect {} tests is {:.3f}s".format(suite.countTestCases(), time.time() - t0))
        print("-" * 50)
        for case in suite:
            if _isnotsuite(case):
                i += 1
                print("{}.{}".format(i, str(case)))
        print("-" * 50)

    def run_suite(self, suite, result, run_func=None, interval=None):
        """基础运行suite方法,支持指定运行方法"""
        log.info('执行测试套件:', suite)
        topLevel = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = topLevel = True

        for index, test in enumerate(suite):
            if _isnotsuite(test):
                setup_ok = run_suite_before_case(suite, test, result)
                if not setup_ok:
                    continue
            log.info('执行用例:', test.id())
            run_func(test, result) if run_func else test(result)  # 可能是suite 可能有异常
            log.info('执行结果:', test.status, '执行时间:', test.duration)
            time.sleep(interval) if interval else None

            if suite._cleanup:
                suite._removeTestAtIndex(index)

        if topLevel:
            run_suite_after(suite, result)
            result._testRunEntered = False

        return result

    # def run_suite_by_class(self, suite, result, run_func=None, interval=None):
    #     suite_list = group_suites_by_class(suite)
    #     for suite in suite_list:
    #         self.run_suite(suite, result, run_func=run_func, interval=interval)

    # def run_suite_in_thread_poll(self, suite, result, threads, interval=None):
    #     poll = ThreadPoolExecutor(max_workers=threads)
    #     self.run_suite(suite, result,
    #                    run_func=lambda case, result: poll.submit(case, result),
    #                    interval=interval)

    # def run_with_timeout(self, test, result, timeout):
    #     print(test, result, timeout)
    #     set_timeout(timeout, result.addTimeout)(test)(result)

    def run(self, suite, callback=None, interval=None):
        result = Result()
        run_func = None
        suite_list = [suite]
        if self.by_class:  # 按类重组suite
            suite_list = group_suites_by_class(suite)

        if self.timeout:
            set_timeout(self.timeout, result.addTimeout)(suite)(result)  # timeout加在最外层的suite上  # FIXME

        if self.threads:
            poll = ThreadPoolExecutor(max_workers=self.threads)
            run_func = lambda case, result: poll.submit(case, result)

        result.start_at = datetime.now()
        for suite in suite_list:
            self.run_suite(suite, result, run_func=run_func, interval=interval)
        result.end_at = datetime.now()
        if callback:
            callback(result)
        return result


class HTMLRunner(Runner):
    def __init__(self, report_file=None, log_file=None,  # 报告文件, 日志文件, 自动创建路径
                 title=None, description=None, tester=None,   # 报告内容
                 template=None, lang=None,  # 模板及语言
                 threads=None, timeout=None, by_class=True,  # 运行选项
                 **kwargs):  # 额外信息
        self.report_file = datetime.now().strftime(report_file or DEFAULT_REPORT_FILE)
        self.log_file = log.file = datetime.now().strftime(log_file or DEFAULT_LOG_FILE)

        self.title = title or DEFAULT_REPORT_TITLE
        self.description = description
        self.tester = tester
        self.template = template or DEFAULT_TEMPLATE
        self.kwargs = kwargs
        super().__init__(threads, timeout, by_class)


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
        # 环境信息
        env_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "python_version": platform.python_version(),
            "env": dict(os.environ),
        }
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
        with open(self.report_file, "w") as f:
            f.write(content)

    def run(self, suite, callback=None, interval=None):
        result = super().run(suite, callback=self.generate_report, interval=interval)
        return result


if __name__ == "__main__":
    pass