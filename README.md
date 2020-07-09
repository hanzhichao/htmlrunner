# htmlrunner

HTMLRunner for unittest

![](./report_detail.png)

## Feature
- 日志
- 添加图片
- [x] 顺序执行/打乱执行
- [x] 多线程
- [x] 按日期命名
- [x] 按测试类统计
- [x] 统计图
- [x] 执行时间
- [x] 超时时间设置
- [x] 环境信息
- [x] extra信息
- [x] 自定义模板
- [x] 获取代码数据
- [x] tag实现
- [x] level实现
- [x] failfast
- [x] order实现
- [x] 附加图片
- [x] timeout实现
- [ ] 多次运行结果
- [ ] 性能分析
- [ ] 不稳定用例
- [ ] 标记bug
- [ ] 增加稳定性
- [ ] 异常解释
- [ ] 多语言
- [ ] 发送邮件
- [ ] email支持格式
- [ ] 发送到飞书、钉钉、企业微信，短信（仅summary),Confluence  (hook)
- [ ] 失败重试
- [ ] 拦截请求和响应
- [ ] 识别times
- [ ] 识别依赖
- [ ] register每一步result
- [ ] XML报告
- [ ] 全局order


## Install
```
pip install htmlrunner
```

## Simple Use
```python
from htmlrunner import HTMLRunner
suite = unittest.defaultTestLoader.discover('.')
HTMLRunner(output="report_%Y%m%d_%H%M%S.html",
            title="测试报告",
            description="测试报告描述", tester='Hzc').run(suite)

```


## Todo
- [ ] setup module timeout问题
- [x] not run test duration问题
- [ ] 模板中直接遍历test_cases取不到用例状态等