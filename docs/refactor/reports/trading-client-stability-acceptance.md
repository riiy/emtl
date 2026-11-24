# TradingClient 稳定性验收（Phase 0）

状态：Phase 0 功能验收 PASS（维护者确认），停止本阶段 SDK 优化。详细实测数据未提供，正式发行验收另行执行。

## 已核实证据（2026-11-24）

- [PR #37](https://github.com/riiy/emtl/pull/37) 已合并，head `4244f56e84aca34e3bdc330981c5b617f73d7fec`，master 合并提交 `d3027dce051a1faed9f16d272d0032660c10d540`。
- 最终 PR CI：[Build](https://github.com/riiy/emtl/actions/runs/45317760592)、[Offline](https://github.com/riiy/emtl/actions/runs/45317760064)、[Package Alpha](https://github.com/riiy/emtl/actions/runs/45317759943) 均为 success。
- 合并后精确 SHA master CI：[Build](https://github.com/riiy/emtl/actions/runs/45317984764)、[Offline](https://github.com/riiy/emtl/actions/runs/45317986961)、[Package Alpha](https://github.com/riiy/emtl/actions/runs/45317984774) 均为 success。
- 独立 Review：维护者确认通过；本记录未取得独立 Review 原文。
- 真实账户验收：维护者于 2026-11-24 确认完成，并在发布准备审查中指出下列四项尚未勾选，按维护者确认归档完成状态。未提供实际轮数、成功/失败计数、测试版本、OS/Python 或逐项脱敏日志；勾选表示维护者确认验收完成，不是独立测量或复核的证据，不推定具体成功率。

## 范围

仅为显式 TradingClient 增加有限 HTTP 连接/读取超时（5/30 秒，验证码读取 60 秒）和有限验证码识别次数（默认 5 次）。旧模块级 API 行为保持不变，不自动重发交易、不增加自动重登录、不改变委托响应语义。超时不代表端到端绝对截止时间。交易 POST 尝试之后的超时仍属于 TradeOutcomeUnknown。

## 验收门槛

- [x] CPython 3.11、3.12、3.13 离线测试通过；使用合成账户和禁网测试。
- [x] tox -e check 与 tox -e docs 通过。
- [x] GitHub Actions 和独立 Review 通过。
- [x] 维护者确认受控环境真实登录与只读查询验收完成（原门槛至少 10 轮）。实测轮数、成功/失败计数、版本、Python、平台及脱敏异常类别未提供，不能独立核实；确认日期 2026-11-24。不归档账户信息或响应原文。
- [x] 维护者确认只读验收范围完成：资金/持仓、当日及历史委托、当日及历史成交；资金流水按需查询。未独立复核逐项日志。
- [x] 按只读验收约定，不执行真实下单或撤单；CI 使用合成账户及禁网环境，不注入真实凭证。
- [x] 维护者确认验收完成，未报告阻塞问题；停止 Phase 0 SDK 优化，后续仅在新证据表明存在阻塞时另行评估。

不声明生产或真实成交可靠性。v0.3.1 候选的精确 SHA CI、发行包审计、上传审批和发布后验收另行完成；本文件不是发布成功证明。
