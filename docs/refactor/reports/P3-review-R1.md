# P3 首次独立 Review：R1

来源：维护者明确授权的只读独立审查子会话 `ses_e4a54104dffeFedISc2HJcgid3`。受审HEAD为`ea81a07f3b54cb7255ba0ae55a7bf5a8dbc55884`的未提交工作区。

## 结论

- 源码/本地验收：**FAIL**，1项MEDIUM公开异常分类缺陷。
- 既有离线测试/证据一致性：PASS，但存在覆盖缺口。
- 远端最终提交双CI/Artifact/Tree：NEEDS EVIDENCE。
- 总体：**FAIL，不得关闭P3**。

## R1：响应处理的BrokerHTTPError被误认为交易HTTP状态

受审`src/emtl/client.py:203–212`将query与结果处理放入同一try，`except BrokerHTTPError`也覆盖JSON、真值和订单日志等响应处理。

独立审查实际以READY客户端、真实公开生产链、合成Session及真实logging.Handler复现：POST返回HTTP200，JSON1返回`{}`，handler.emit在固定订单事件抛`BrokerHTTPError(503)`。实际Unknown字段为`create_order/http_status/503`，契约应为`create_order/response_error/None`；响应状态200、JSON调用1次、POST1次。未发现因此重发，但机器可读分类错误。既有log测试只抛ValueError，未检出类型碰撞。

最小建议：仅在query交换阶段特殊处理BrokerHTTPError；query正常返回后的普通异常统一response_error/None。补真实日志handler与JSON抛BrokerHTTPError回归，保持POST一次。不改旧core、成功返回、锁或重试策略。

实现遵循了原计划§6.2宽捕获伪代码，但与§5.1及公开阶段契约冲突；应优先满足契约，不能因遵循伪代码签认通过。

## 独立执行与边界

审查完整读取需求/计划/契约/源码/测试/隔离设施，检查8个tracked修改、6个untracked与空staged；完整sandbox套件两次分别442 passed（11.60s、9.62s），Ruff和diff检查通过。10种变异独立内存复跑均被业务失败检出，预期失败数2/2/2/2/2/2/4/4/4/1，无collection/setup/teardown错误；未覆盖原JUnit或日志。

独立核验46文件源码/config哈希、32份Linux证据哈希，三份LinuxJUnit各442项0失败/错误/跳过；原P2的350、P1的168节点保留；S1红灯21通过/4预期失败、S2/S3/final/resume分别199/176/442/442项；真实tox隔离前置检查有效。既有绿灯不消除R1。

审查未修改项目文件，未访问网络/真实账户/券商/真实OCR，未触发CI；未重建/重跑Linux，未独立重跑tox、Black或远端工作流。独立意见要求修复R1并更新最终代码/测试/镜像/哈希证据后复审，再由维护者控制Git交付及远端核验。
