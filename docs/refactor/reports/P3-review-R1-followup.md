# P3 R1 独立只读复审报告

来源：维护者明确授权的独立只读审查子会话`ses_e4a54104dffeFedISc2HJcgid3`，在首次FAIL后对R1修复及最终本地证据复审。以下记录独立审查实际结论和执行范围，Build仅负责归档；首次意见[P3-review-R1.md](P3-review-R1.md)保留不变。

## 结论

| 范围 | 结论 |
| --- | --- |
| R1缺陷 | **已关闭，限本次受审快照** |
| 源码/本地独立Review | **PASS** |
| 最终提交远端双workflow/Artifact/head_sha/Tree | **NEEDS EVIDENCE** |
| P3总体验收 | **NEEDS EVIDENCE，不得宣布最终PASS或关闭P3** |

本次未发现其他确定缺陷。结论来自实际代码检查、独立反例复现、内存变异及原始证据核验，不依赖Build自评。

## 1. 受审范围与差异

- 分支`refactor/p3-trade-errors`，HEAD`ea81a07f3b54cb7255ba0ae55a7bf5a8dbc55884`，实现未提交。
- 受审时8个tracked修改、7个untracked、staged为空；完整检查status、tracked/staged diff及新增交付文件，含首次Review归档、计划§22、验收报告§9和契约补充。
- 与首轮受审46文件快照相比，只有`src/emtl/client.py`和`tests/test_trade_errors.py`改变。
- 独立在内存还原旧helper后，完整client.py的SHA256与首轮快照相同；移除新增logging import与四分支回归后，旧测试文件SHA256完全匹配。没有夹带其他生产改动或弱化原测试。
- 首次Review摘要准确保留FAIL；计划如实记录伪代码与阶段契约冲突，没有改写历史。

## 2. R1修复确认

`src/emtl/client.py:202–220`将query与结果处理分为两个捕获范围：query阶段保留BrokerHTTPError特殊处理；正常返回后的普通结果处理异常统一response_error/None；两处保留attempted守卫，不捕获BaseException。

独立重新通过真实公开生产链、合成Session及真实logging.Handler执行原反例，确认：

```text
HTTP 200
TradeOutcomeUnknown(create_order, response_error, None)
JSON调用1次；POST1次；GET0次
READY/token保持
__cause__ is None；__suppress_context__ is True
```

新回归`tests/test_trade_errors.py:365–406`的json1/json2/log/text四分支确实走真实公共链，log为真实handler，检查字段、HTTP200、解析次数、POST1/get0及认证状态。随后仅在独立进程内恢复首轮宽捕获实现，四分支全部因http_status不等于response_error而失败，无collection/setup/teardown错误，证明能检出R1。

## 3. 独立实际执行

统一系统禁网、禁止字节码和pytest缓存，不生成或覆盖报告：

```bash
env -u EM_USERNAME -u EM_PASSWORD \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS= \
  sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .venv/bin/python -B -m pytest -p no:cacheprovider -q
```

| 检查 | 实际结果 |
| --- | --- |
| 完整套件 | 446 passed，10.03s |
| 变异后完整正常套件 | 446 passed，7.60s |
| 原始真实handler反例 | 修复验证通过 |
| 恢复旧宽捕获的R1变异 | 四分支均被字段断言检出 |
| 原有10种内存变异独立复跑 | 全部检出，业务失败数2/2/2/2/2/2/4/4/4/1 |
| Ruff（含归档脚本，no-cache） | 通过 |
| tracked/staged diff --check | 通过 |

全部变异无collection/setup/teardown错误，未以语法或导入失败冒充检出，未覆盖原JUnit/日志。

## 4. 最终本地证据独立核验

- 重算当前46文件，与`dist/p3-r1/source-sha256.json`及最终镜像提取清单完全相同。
- 最终镜像`sha256:b01c9f2ffbcb08826e5d99be4311bbb5bfc3dbc1ec84e390867199afa9f69dfd`，18层的前15层与首轮固定准备镜像完全一致；driver CMD、依赖/config未变。
- 最终Linux33份证据哈希、首轮Linux32份证据哈希均有效。
- 原Dockerfile退出2日志确为pip下载virtualenv超时，属于准备失败；禁网COPY薄层构建退出0。层前缀、源码哈希及完整最终测试支持该本地准备偏差可接受，但不能替代最终远端原CI构建。

| 原始证据 | 独立解析结果 |
| --- | --- |
| R1 red JUnit | 4个字段分类失败，0error/skip |
| targeted JUnit | 219项通过 |
| sandbox tox final JUnit | 446项，0failure/error/skip，32.369s |
| Linux默认入口 | 446项，0failure/error/skip |
| Linux仓库外入口 | 446项，0failure/error/skip |
| Linux显式tests入口 | 446项，0failure/error/skip |

最终本地与Linux三份完整JUnit节点集一致；原P2的350、首轮P3的442、P1的168节点全部保留。inspect确认最终容器NetworkMode=none、无挂载、退出0，宿主和驱动各步骤均退出0；OS探针有效，真实tox隔离前置检查退出0且先于测试结果。两平台coverage原始JSON一致：行444/468、分支99/110，不作为单独通过依据。

## 5. 兼容与风险保护

静态检查与完整回归未发现以下保护退化：前置认证/参数失败不误标Unknown、局部发送边界/唯一POST不变；无自动重试/重登重放/补偿查询撤单/隐式交易重定向；双JSON和第二对象身份、Status=-1/list/None、FalseResponse、撤单文本返回保持；旧API/CLI精确签名、旧裸raise及活跃except原异常对象保持；账户锁覆盖POST/解码/转换、真实竞争与失败释放测试通过；BaseException、安全字段、from None、标准traceback及SDK日志保护保持。

可信工厂、无隐藏重发、非HTTP原异常可能含秘密、内存context/APM不受全面清洗等边界仍须保留，Unknown不是重发许可。

## 6. 未执行边界与剩余工作

独立复审未修改、暂存、提交项目文件或原始证据；未联网、访问真实账户/券商/OCR、fetch/push或触发CI；未重新运行Docker、tox或Black，这些部分只核验保存的原始记录（Black日志34文件无需改动）。

**R1在当前快照关闭，源码/本地独立Review为PASS。** 后续仍须维护者控制Git交付，核对最终提交双workflow、Artifact、head_sha和Tree；完成前P3总体验收保持NEEDS EVIDENCE。
