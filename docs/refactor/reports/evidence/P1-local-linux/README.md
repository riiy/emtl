# P1 本地 Linux 历史证据

这些文件归档本地历史构建和 Review 验证，不是 GitHub Actions artifacts，不代表最终提交已完成 P1 验收。详细命令和结论见 [P1-acceptance.md §8](../../P1-acceptance.md#8-本地-linux-验证历史结果补记)。旧日志未被覆盖。

## 身份及结果

- Git HEAD：`2d8929b6b3df88131419e89b868a4cdb0b81c7a3`，实现还在未提交工作区；不能把镜像内容等同于 HEAD。
- 本地镜像 ID：`sha256:09508f8f6fc8819496d815cad28e5fe18963ce4635aad23beef3c537861ceb1e`，`linux/amd64`，标签 `emtl-p1-offline:repair`。
- 构建命令：`docker build --file ci/offline.Dockerfile --tag emtl-p1-offline:repair .`；cwd `/Users/lld/emtl`，退出 0（原始 result JSON）。
- 历史运行：`docker run --rm --network none emtl-p1-offline:repair`；同一宿主 cwd，退出 0（Review 工具执行结果、本次用户提供的已知证据）；原始 stdout 本身记录各子命令的 `EXIT 0`，不单独记录 docker CLI 的退出状态。
- 独立 OS 探针、tox 凭证隔离通过；默认、仓库外不同顺序、显式目录三轮各 168 passed。

## 原始文件来源和完整性

Linux 输出与构建 result JSON 是逐字节副本。构建日志仅将第 5 行末的终端 `\r\r\n` 换行序列规范化为 LF，其他内容不做重排、截断或版本号替换；原始 `dist/` 日志不变。读取确认只含合成测试值和工具诊断，没有真实交易账户秘密。

| 归档文件 | 原始位置 | 字节数 | SHA256 |
| --- | --- | --- | --- |
| [`build-output.txt`](build-output.txt) | `dist/p1-repair/docker-build.log`（仅换行规范化） | 10352 | `6d762b9d756cab10c5205b06b027ea65b90570564bc698b685dda1b78fa17b23` |
| [`docker-build-result.json`](docker-build-result.json) | `dist/p1-repair/docker-build-result.json` | 186 | `b1e9a4a5a155853134e4b9876400ab473d5c1ed3c260427947b48bf4f12269a0` |
| [`linux-run-output.txt`](linux-run-output.txt) | `/Users/lld/.local/share/opencode/shell/5deda5dfb5cf6ac4b518e3ef1e5fc8f0cedcf0fb/sh_1afdd2ccb001T740pikB6VUYjz.out` | 40309 | `9c3e03e0b5cd79674fef34032012d7d181029424a0d01b98d24907a57366c839` |

构建日志原始文件仍为 10354 字节，SHA256 `4646ebf64861d885e4f332bd7d3ff3ad49c531267b322d57ef3f8ecab68eb6e5`；可通过移除原文件该处的两个 `\r` 验证归档副本，没有丢弃诊断文本。

可在仓库根校验：

```bash
shasum -a 256 docs/refactor/reports/evidence/P1-local-linux/build-output.txt docs/refactor/reports/evidence/P1-local-linux/docker-build-result.json docs/refactor/reports/evidence/P1-local-linux/linux-run-output.txt
```

## 版本及关键行号

以下行号指归档日志原文，不是根据宿主环境或浮动镜像标签推断：

- `linux-run-output.txt:5`：Python 3.11.18、pytest 9.2.0、pytest-cov 7.1.0、coverage 7.17.2 的版本 JSON。
- `build-output.txt:96`：安装 tox 4.67.12；`:145–146` 构建成功。
- `linux-run-output.txt:1–3`：独立 OS 网络探针、退出 0。
- `linux-run-output.txt:19–21`：tox 启动 pytest 前的凭证隔离检查、退出 0。
- `linux-run-output.txt:7,218–222`：默认 tox 完整命令、168 passed、退出 0。
- `linux-run-output.txt:223,402–403`：仓库外不同顺序完整命令、168 passed、退出 0。
- `linux-run-output.txt:404–409`：显式目录完整命令、168 passed、退出 0。
- `linux-run-output.txt:203–217`：Linux 控制台覆盖率，整体 88.31%，core 125 条语句/32 个分支、100.00%。

Ruff/Black 的既有通过是 macOS 记录；不得根据本目录将其改称为 Linux 检查。

## 快照差异与限制

历史归档时的源码/测试/CI 配置与固定镜像 ID 只读比较 37 个文件，36 个相同；唯一不同 `tests/test_wrapper_contract.py` 将 `QUERY_CALLS + [...]` 改成 `[*QUERY_CALLS, ...]`。这是当时的快照比较，不是本次重做的当前工作区比较；后续 SCM CI 修正及最终验证见验收报告 §9。生成 `_version.py`、构建后补写的文档、其他非代码构建材料不在这 37 个文件的比较范围内。

历史容器使用 `--rm`；其 Linux JUnit、coverage XML/JSON、tox-result、versions/commands JSON 未导出，目前不存在可归档原件。本目录保存的是现有控制台/构建日志，不伪造那些 JSON/XML。宿主 `dist/p1-repair/` 中现有同名文件属于 macOS 运行。

历史归档时的状态为：“远端 GitHub Actions run、runner NetworkMode inspect 证据、报告复制/清理的实际结果与 artifacts URL 均待完成；本地成功不能替代它们。P1 状态仍为 NEEDS EVIDENCE。”最新远端证据现已补齐，见下方及[验收报告 §9](../../P1-acceptance.md#9-pr-3-合并与远端验收证据)，不将该历史状态当作最新结论。

## 最终文档收口核验（追加）

- 本次实际读取本目录四个文件，复算三个原始日志/JSON 的字节数和 SHA256，均与上表相符；三个文件未改。README 是维护中的来源说明，不把其修改后的哈希伪称为历史日志哈希。
- `build-output.txt` 与当前 `dist/p1-repair/docker-build.log` 经已声明的换行规范化后一致；`docker-build-result.json` 与其当前 `dist/` 源文件逐字节一致。
- Linux 原 OpenCode shell 临时源路径现已不存在，不能重新与该源比较；归档副本仍完整且哈希与历史记录一致，内有五个 `EXIT 0`、三轮各 168 passed。此限制不等于远端报告缺失，也不把宿主 macOS JSON 当作 Linux 原件。
- 逐份检查未发现真实账号、密码、Cookie/Authorization 值或完整交易响应；测试 nodeid 中的 `OLD`、`first`、`second` 等均是合成 token 参数。来源路径仅标识历史宿主/容器位置。
- 所有本地文件链接均应随目录一起交付。远端身份及内容依据维护者独立核实提供的信息，未重新联网查询链接有效期；artifact 不冒充本目录的历史镜像产物。

### 远端证据索引

- [Offline Run 42199620264](https://github.com/riiy/emtl/actions/runs/42199620264)、[Build Run 42199620359](https://github.com/riiy/emtl/actions/runs/42199620359)：均为 `pull_request`，`head_sha=8d0a2303d13a2f9d0c9aafae2f1bbe26bd2ade5d`，`conclusion=success`。
- [Artifact 13493921728](https://github.com/riiy/emtl/actions/runs/42199620264/artifacts/13493921728)：属于 Offline Run，三份 JUnit 各 168 tests、0 failures、0 errors，NetworkMode=none、container-exit-code=0，host-status 六项均为 0。
- 行覆盖率 **88.48%**（169/191）、分支覆盖率 **87.50%**（35/40）、综合覆盖率 **88.31%**（204/231）；远端 `coverage.json` 字段摘录见验收报告 §9.3。
- merge commit `318fb45a5a279d103049c5adc1974e714847df4e` 与受测提交的 Tree SHA 均为 `55f8640c1cb3711ce7ac8d31865752fb242eda0a`，本次本地 Git 实查一致。

### 版本控制交付

本目录四个文件均需纳入版本控制；本次检查仍未跟踪，且不在原 merge commit 中，不能声称 PR #3 已交付这些附件。本次只更新本 README，不重写原始日志/JSON、不自动暂存或提交。连同批准计划及验收报告的六文件暂存建议见[验收报告 §10](../../P1-acceptance.md#10-文档归档核验与交付清单)。最终独立 Review PASS 不由本次文档补记代签。
