import platform
from datetime import datetime, date, timedelta
import os
import time
import unittest
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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

class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, timedelta):
            return obj.seconds

        return json.JSONEncoder.default(self, obj)

class Runner(object):
    def __init__(self,
                 threads=None,
                 timeout=None,  # todo 配置到用例docstring中
                 interval=None,  # todo remove
                 failfast=False,
                 ensure_sequence=True,
                 output_dir=None,
                 **kwargs):
        self.threads = threads
        self.interval = interval
        self.timeout = timeout   # 每个用例的执行时间
        self.failfast = failfast
        self.output_dir = output_dir
        self.kwargs = kwargs
        self.ensure_sequence = ensure_sequence  # 确保运行顺序

    def collect_only(self, suite):
        loader = Loader(suite=suite)
        t0 = time.time()
        i = 0
        suite = loader.fsuite
        print("Collect {} tests is {:.3f}s".format(suite.countTestCases(), time.time() - t0))
        print("-" * 50)
        for case in suite:
            if isnotsuite(case):
                i += 1
                print("{}.{}".format(i, str(case)))
        print("-" * 50)

    def run_suite(self, suite, result, run_func=None, interval=None):
        topLevel = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = topLevel = True

        for index, test in enumerate(suite):
            if isnotsuite(test):
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
        loader = Loader(suite=suite)

        suite_list = loader.gsuite
        for suite in suite_list:
            self.run_suite(suite, result, run_func=run_func, interval=interval)

    def run_suite_in_thread_poll(self, suite, result, thread_num=3, interval=None):
        poll = ThreadPoolExecutor(max_workers=thread_num)
        tasks = []
        def run_in_poll(case, result):
            task = poll.submit(case, result)
            tasks.append(task)

        self.run_suite(suite, result, run_func=run_in_poll, interval=interval)
        return tasks

    def run(self, suite, callback=None):
        result = Result(output_dir=self.output_dir, failfast=self.failfast)
        result.start_at = datetime.now()

        if self.ensure_sequence:
            loader = Loader(suite=suite)
            suite = loader.osuite

        if self.threads:
            tasks = self.run_suite_in_thread_poll(suite, result, thread_num=self.threads, interval=self.interval)
            for task in as_completed(tasks):
                task.result()
        else:
            self.run_suite(suite, result)
        result.end_at = datetime.now()
        if callback:
            callback(result)
        return result


class HTMLRunner(Runner):
    def __init__(self, report_file=None, log_file=None,  output_dir=None, # 报告文件, 日志文件, 自动创建路径
                 title=None, description=None, tester=None,   # 报告内容
                 template=None, lang=None,  # 模板及语言
                 verbosity=2, failfast=False,
                 threads=None, timeout=None,  # 运行选项
                 interval=None,
                 **kwargs):  # 额外信息
        self.verbosity = verbosity
        self.failfast = failfast
        self.interval = interval
        self.output_dir = output_dir
        self._report_file = report_file
        self._log_file = log_file

        self.title = title or DEFAULT_REPORT_TITLE
        self.description = description
        self.tester = tester
        self.template = template or DEFAULT_TEMPLATE
        self.kwargs = kwargs
        super().__init__(threads, timeout, interval, output_dir=output_dir)
        self._handle_output_dir()

    def _handle_output_dir(self):
        now = datetime.now()
        self.report_file = now.strftime(self._report_file or DEFAULT_REPORT_FILE)
        self.log_file = now.strftime(self._log_file or DEFAULT_LOG_FILE)

        if self.output_dir:
            if not os.path.isdir(self.output_dir):
                os.makedirs(self.output_dir)
            self.report_file = os.path.join(self.output_dir, self.report_file)
            self.log_file = os.path.join(self.output_dir, self.log_file)
            self.cache_file = os.path.join(self.output_dir, '%s.json' % now.strftime('%Y%m%d%H%M%S'))
        log.file = self.log_file

    def _get_context(self, result):
        """组装上下文信息"""
        test_classes = result.sortByClass()

        # 结果统计
        result_summary = {
            "report": {
                "title": self.title,
                "description": self.description,
                "tester": self.tester
            },
            "stat": {
                "total": result.totol,
                "run_num": result.testsRun,
                "pass_num": len(result.success),
                "fail_num": len(result.failures),
                "skipped_num": len(result.skipped),
                "error_num": len(result.errors),
                "xfail_num": len(result.expectedFailures),
                "xpass_num": len(result.unexpectedSuccesses),
                "rerun_num": 0,
            },
            "time": {
                "start_at": result.start_at,
                "end_at": result.end_at,
                "duration": result.end_at - result.start_at,
            },
            "platform":
                {
                "platform": platform.platform(),
                "system": platform.system(),
                "python_version": platform.python_version(),
                "env": dict(os.environ),
            },
            "suites": test_classes,

        }
        context = {}
        # 环境信息
        [context.update(info) for info in (result_summary, self.kwargs)]  # 额外变量

        return context

    def _cache_context(self, context):
        """缓存上下文文件"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, cls=MyJSONEncoder, ensure_ascii=False, indent=2)

    def _stat_cache(self):
        files = os.listdir(self.output_dir)  # todo 确保output_dir存在
        cache_files = [file_name for file_name in files if file_name.endswith('.json')]
        cache_files.sort()
        cache_files = cache_files[-10:]
        data = {
            'title': [file_name.strip('.json') for file_name in cache_files],
            'pass': [],
            'fail': [],
            'error': [],
            'skipped': [],
        }
        for file_name in cache_files:
            file_path = os.path.join(self.output_dir, file_name)
            with open(file_path, encoding='utf-8') as f:
                run_data = json.load(f)
            data['pass'].append(run_data.get('pass_num'))
            data['fail'].append(run_data.get('fail_num'))
            data['error'].append(run_data.get('error_num'))
            data['skipped'].append(run_data.get('skipped_num'))
        return data

    def generate_report(self, result):
        context = self._get_context(result)
        self._cache_context(context)
        context['cache'] = self._stat_cache()
        template_path = os.path.join(BASEDIR, 'templates', '%s.html' % self.template)
        with open(template_path, encoding='utf-8') as f:
            template_content = f.read()

        content = Template(template_content).render(context)

        with open(self.report_file, "w", encoding='utf-8') as f:
            f.write(content)

    def run(self, suite, callback=None, interval=None, debug=False):
        result = super().run(suite, callback=self.generate_report)
        return result


if __name__ == "__main__":
    pass