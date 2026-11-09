# P4 发布故障桌面推演（2026-11-08）

> **2026-11-09 收尾校正（当前状态）**：本报告的推演和风险清单形成于 2026-11-08；文末“无 reviewers、依赖安全公告未完成”的断言仅描述当时状态，不代表当前 master。PR #21、#22 后运行依赖已调整为 `cryptography==50.0.2`、`requests==2.33.1` 并完成对应回归；PR #23 后 `pypi` Environment required reviewer 的**静态配置**已有维护者提供的证据，但无上传审批探针尚未实际验证。2026-11-09 最新 master `dbf13b49dac3b3e56d0087d4c426a5075ddc6d20` 的 Build / Offline / Package Alpha 均为 success。**P4 总体仍 NEEDS EVIDENCE；未执行 Beta/Stable 发布。** 以 [P4 阶段验收](P4-acceptance.md) 和 [依赖审查最终记录](P4-dependency-review.md) 为当前状态依据，保留此文的历史故障推演。

性质：维护流程的合成桌面推演，不是实际发布、yank、GitHub 环境审批或真实交易恢复演练。未创建/推送 tag、上传包、更改 PyPI/GitHub 状态或调用券商。

执行者：本次 Build；实际发布/事故决策责任人：仓库维护者。输入：批准的 P4 Plan、`docs/releasing.rst`、P0–P3 契约、本次合成 release gate/manifest 失败注入测试。

| 合成情景 | 推演动作与停止条件 | 结果与局限 |
| --- | --- | --- |
| Build/Offline 失败，或只拿到 PR head 的绿灯 | 不创建正式 tag，不上传；核对最终 master SHA。release_gate 拒绝缺失/失败/跳过/不完整 job 和错误 SHA；修复后重跑必需 CI | 路径明确；只在合成证据中执行失败测试，未触发远端 CI |
| sdist 缺 metadata、wheel 混入凭证文件或哈希漂移 | 在 Alpha 停止，保留失败日志；修复后创建新候选并重跑双安装/smoke；不降低审计 | 本次确实遇到 sdist 裁剪问题并修复；污染/哈希场景由合成 archive 测试拒绝 |
| 上传超时，状态不确定 | 维护者只读查询 PyPI 版本、文件及 SHA256/provenance；没有确认前不重试，不启用 skip-existing，不复用版本号 | 无需真实上传即可验证决策；PyPI 状态不确定的人工操作尚未实演 |
| 已发布 0.3.0 出现交易/敏感信息风险 | 停止推荐受影响操作，私密报告，评估人工 yank/Release 标注，补回归并以新唯一 Hotfix 版本前进修复 | 软件处理不能撤回已接受订单；不自动补单/撤单/对账 |
| 用户要求回退到现有公开 0.2.6 | 不当作默认安全回滚：它早于 P0–P3，无已批准的安全旧版本时暂停受影响用法并修复前进；未来已知良好版本确定后才使用手册中的精确安装命令 | 明确没有当前可推荐的公开安全回退目标，不伪造成功降级证据 |
| PyPI 包正常但 Pages mirror 失败 | 包版本不可覆盖；只修复镜像部署，RTD 仍是 canonical；手动稳定版镜像部署不接收 alpha/beta | 不用文档失败触发第二次包上传；RTD/Pages 真实构建验收仍待远端 |

结论（2026-11-08 推演时）：桌面决策路径可执行，发布门禁与哈希故障有离线测试；**不代替独立 Review、保护环境审批、正式包源安装或真实远端发布后核验**。当时 `pypi` 尚无 reviewers、旧运行依赖公告尚未修复。**2026-11-09 当前结论**：旧 blocker 的定向修复与 reviewer 静态配置证据已有记录，但仍需通过无上传审批探针验证实际 Waiting → Approved 行为；Beta 观察和退出、Stable 单独批准未完成。不得将本桌面推演视为 P4 全部 PASS 或正式发行授权。
