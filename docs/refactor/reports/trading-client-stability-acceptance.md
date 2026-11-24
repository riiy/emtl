# TradingClient 稳定性验收（Phase 0）

状态：代码合并、远端 CI、维护者确认独立 Review 已通过；维护者于 2026-11-24 确认真实账户验收完成，详细实测数据待补录。

## 已核实证据（2026-11-24）

- [PR #37](https://github.com/riiy/emtl/pull/37) 已合并，head `4244f56e84aca34e3bdc330981c5b617f73d7fec`，master 合并提交 `d3027dce051a1faed9f16d272d0032660c10d540`。
- 最终 PR CI：[Build](https://github.com/riiy/emtl/actions/runs/45317760592)、[Offline](https://github.com/riiy/emtl/actions/runs/45317760064)、[Package Alpha](https://github.com/riiy/emtl/actions/runs/45317759943) 均为 success。
- 合并后精确 SHA master CI：[Build](https://github.com/riiy/emtl/actions/runs/45317984764)、[Offline](https://github.com/riiy/emtl/actions/runs/45317986961)、[Package Alpha](https://github.com/riiy/emtl/actions/runs/45317984774) 均为 success。
- 独立 Review：维护者确认通过；本记录未取得独立 Review 原文。
- 真实账户验收：维护者确认完成；没有提供轮数、成功/失败计数、测试版本、OS/Python 或逐项脱敏日志。不能据此宣称至少 10 轮、100% 成功或已验证真实交易。

## 范围

仅为显式 TradingClient 增加有限 HTTP 连接/读取超时（5/30 秒，验证码读取 60 秒）和有限验证码识别次数（默认 5 次）。旧模块级 API 行为保持不变，不自动重发交易、不增加自动重登录、不改变委托响应语义。超时不代表端到端绝对截止时间。交易 POST 尝试之后的超时仍属于 TradeOutcomeUnknown。

## 验收门槛

- [x] CPython 3.11、3.12、3.13 离线测试通过；使用合成账户和禁网测试。
- [x] tox -e check 与 tox -e docs 通过。
- [x] GitHub Actions 和独立 Review 通过。
- [ ] 维护者在受控环境完成至少 10 轮真实登录和只读查询，记录测试版本、Python、平台、日期、成功/失败计数、脱敏异常类别；不将账户信息或响应原文上传。
- [ ] 只读范围包含资金/持仓、当日及历史委托、当日及历史成交；可按需查询资金流水。
- [ ] 不执行真实下单或撤单，无真实凭证进入 CI。
- [ ] 如验收失败，仅对有证据的阻塞问题修复；通过后停止 Phase 0。

不声明生产或真实成交可靠性。v0.3.1 候选的精确 SHA CI、发行包审计、上传审批和发布后验收另行完成；本文件不是发布成功证明。
