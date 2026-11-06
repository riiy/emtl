# P1 限定修复验收记录

## 1. 基线、范围与结论

- 日期：2026-11-06。
- Git HEAD：`2d8929b6b3df88131419e89b868a4cdb0b81c7a3`；分支 `refactor/p1-offline-tests`。实现仍在未提交工作区，HEAD 不是包含本次修复的提交。
- 默认工作目录：`/Users/lld/emtl`；全部相对报告路径均以此为根。
- 依据：现有批准的 P1 计划及人类针对 FAIL 的六项限定修复授权；未重新规划阶段。
- 修复前基线为 91 项；本轮完整 tox 和仓库外不同顺序运行均为 **168 项通过**。数目增加不代替风险行为断言。
- `src/emtl/` 无修改；公共 API/CLI 兼容性测试保留。不调用真实交易，不使用真实账户，不增加重试，不进入 P2/P3。
- **P1 总体仍为 NEEDS EVIDENCE**：远端 GitHub Actions 尚未运行，独立复审未获 PASS。Docker 本地实际构建结果在本记录后续节单独列明，不将静态测试等同于构建成功。

## 2. 六项修复及行为证据

| 项目 | 本地检查 | 测试/实现位置与结果 |
| --- | --- | --- |
| 1 Docker 构建配置 | PASS（静态配置）；实际构建另见第 7 节 | `.coverage*` 改为 `.coverage` 和 `.coverage.*`；`.coveragerc` 不再匹配。`test_offline_ci.py::test_docker_copy_sources_and_coverage_config_are_not_ignored` 对照全部 COPY 源路径的存在性与当前简单 ignore 规则；Dockerfile 增加复制该静态回归需要的 `.dockerignore` |
| 2 异常契约 | PASS | `test_core.py` 的行情 Timeout/ConnectionError/HTTP/非法 JSON 均传播且一次 GET；六查询失败集合；`test_orders.py` 撤单 text 属性失败传播且一次 POST；`test_wrapper_contract.py` 八个包装层 None/假值及 JSON 对象透传；`test_auth.py`、日志测试补认证/响应处理异常、请求顺序和秘密哨兵 |
| 3 Actions 清理 | PASS（安全失败注入） | 原工作流 run block 由 Bash `-e -o pipefail` 执行；EXIT trap 始终尝试 logs、inspect、cp、rm。先保存整个 PIPESTATUS 数组，原启动/容器失败码优先，原过程成功时报告复制/清理失败也不能变绿。8 个 shell 场景通过，另有驱动成功/失败/超时记录 3 例 |
| 4 根 conftest 生命周期 | PASS | `test_offline_guard.py::test_root_conftest_initialization_and_unconfigure_restore` 的两种合成父环境，真正经过 pytest 初始化、collection 和 unconfigure；验证凭证隔离/恢复、假 OCR 及网络函数对象恢复。恢复后只能触达预置底层哨兵，无真实连接 |
| 5 系统禁网 CI | NEEDS EVIDENCE（远端） | 保留联网构建、`--network none`、NetworkMode 精确检查及独立 Linux OS 探针；驱动保存 versions/commands/合成环境/日志/JUnit/coverage。远端 artifacts 链接：无，未 push 或触发远端 workflow |
| 6 验收记录 | PASS（本地记录） | 本文记录真实命令、工作目录、版本、合成环境、退出码和原始报告路径；远端缺证据项不填写虚构链接 |

### Mock 边界与变异检验

- 行情、认证、错误传播、撤单文本异常和请求次数证据均真实执行目标公共 API 及内部请求/检查链，只替换 HTTP、OCR、随机数、加密依赖或 HTTP response 属性。
- `_query_something()` 当前不能自然返回 None：底层 POST 返回 None 会先在 `_check_resp()` 抛 AttributeError，相关端到端测试仍保留。单独的 `wrapper_seam_none` 用例只替换包装层的这个依赖，真实执行包装函数，不将其计为 HTTP 或订单无重试证据。这是批准计划 §5.1 明确允许的合成分支。
- 假值 response 用 status=200 的测试 Response 子类构造，真实执行 `_query_something()`，八个包装 API 均返回 None、POST 一次、不解析 JSON。
- 对行情已知变异进行一次仅在子进程内存生效的替换：捕获 Timeout/ConnectionError 返回 None。新增的两项回归均报 `DID NOT RAISE`，变异进程退出 1；正常源码对应测试及全套均通过。没有修改源码文件。
- 无 P0 测试被删除。原查询错误测试扩展至六 API，其参数化 nodeid 增加 name/args，原 query_orders 的错误场景保留。其他 P0 nodeid 与保护继续保留。

### 本轮修改文件

`.dockerignore`、`ci/offline.Dockerfile`、`.github/workflows/offline-tests.yml`、`ci/run_offline_tests.py`；`tests/helpers.py`、`tests/test_core.py`、`tests/test_auth.py`、`tests/test_orders.py`、`tests/test_logging_safety.py`、`tests/test_offline_guard.py`；新增 `tests/test_wrapper_contract.py`、`tests/test_offline_ci.py`；本文。

未改根 `conftest.py` 或生产代码。新增两个测试文件是本次明确授权的契约/失败注入验证，不引入新测试框架或调度脚本。整个 Git 工作区还包含上一轮 P1 已存在的修改，交付时需一并审查 tracked/staged/untracked，不能只提交本轮差量。

## 3. 工具与证据目录

本机 macOS：Python **3.11.14**、pytest **9.2.0**、pytest-cov **7.1.0**、coverage **7.17.2**、tox **4.67.12**、Ruff **0.4.1**、Black **24.4.0**。

版本原始记录：`dist/p1-repair/versions.json`。生成命令（退出 0）：

```bash
.venv/bin/python -c 'import json,platform; from importlib.metadata import version; from pathlib import Path; data={"python":platform.python_version(),"packages":{n:version(n) for n in ("pytest","pytest-cov","coverage","tox","ruff","black")}}; Path("dist/p1-repair/versions.json").write_text(json.dumps(data,indent=2)); print(json.dumps(data,indent=2))'
```

所有 `dist/` 报告是本次机器的原始证据，被 Git ignore，不是已上传远端 artifacts。需由维护者保留目录或用远端 CI artifacts 固化，不能依赖临时文件永久存在。

## 4. 实际验证命令、工作目录、退出码

以下命令无省略参数。含管道的命令先启用 `pipefail`，所以 tee 不会掩盖测试失败。

### 4.1 独立 macOS 断网探针

工作目录 `/Users/lld/emtl`：

```bash
set -o pipefail
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -c 'import socket; s=socket.socket(); s.connect(("127.0.0.1", 9))' 2>&1 | tee dist/p1-repair/macos-network-probe.log
```

实际退出 **1**，`PermissionError: Operation not permitted`，是预期的 OS 阻断，不是测试失败。只尝试 loopback，不访问外部服务。

### 4.2 首批契约/生命周期验证

工作目录 `/Users/lld/emtl`：

```bash
set -o pipefail
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest tests/test_core.py tests/test_auth.py tests/test_orders.py tests/test_wrapper_contract.py tests/test_logging_safety.py tests/test_offline_guard.py -vv --junitxml=dist/p1-repair/contracts-junit.xml 2>&1 | tee dist/p1-repair/contracts.log
```

退出 **0**，115 passed；此批早于六查询错误参数化扩展。最终完整结果见 §4.5。

### 4.3 CI shell/驱动失败注入

工作目录 `/Users/lld/emtl`：

```bash
set -o pipefail
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest tests/test_offline_ci.py -vv --junitxml=dist/p1-repair/ci-injection-fixed-junit.xml 2>&1 | tee dist/p1-repair/ci-injection-fixed.log
```

退出 **0**，12 passed。命令中的 docker/tee 是测试子进程函数替身，不访问 Docker daemon 或网络。初次使用相同测试选择、输出 `ci-injection-junit.xml`/`ci-injection.log` 时退出 **1**（11 passed/1 failed）：tee 故障替身误作用于早于启动的 NetworkMode 日志，修正注入位置后以上重跑通过。初次报告仍保留，没有删除失败证据。

### 4.4 行情吞异常变异检验

工作目录 `/Users/lld/emtl`：

```bash
set -o pipefail
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python - <<'PY' 2>&1 | tee dist/p1-repair/price-mutation.log
import pytest

class SwallowTransport:
    def pytest_collection_modifyitems(self, session, config, items):
        from emtl import core
        import requests
        original = core._query_snapshot
        def snapshot(*args, **kwargs):
            try:
                return original(*args, **kwargs)
            except (requests.Timeout, requests.ConnectionError):
                return None
        core._query_snapshot = snapshot

raise SystemExit(pytest.main([
    'tests/test_core.py', '-k', 'price_transport_error_is_not_nan', '-vv',
    '--junitxml=dist/p1-repair/price-mutation-junit.xml'
], plugins=[SwallowTransport()]))
PY
```

实际退出 **1**，2 failed，均为 `DID NOT RAISE`。这是预期检出变异；变异仅存在该进程，不在全套测试/源码中保留。

### 4.5 完整 tox、凭证隔离与覆盖率

工作目录 `/Users/lld/emtl`；全部父凭证均为下列明确合成值，未读取或打印真实凭证：

```bash
set -o pipefail
PIP_NO_INDEX=1 TOXPYTHON="$PWD/.venv/bin/python" EM_USERNAME=P1_FAKE_USER EM_PASSWORD=P1_FAKE_PASSWORD EM_P1_SENTINEL=P1_FAKE_SENTINEL P0_FAKE_ACCOUNT_CREDENTIAL=P1_FAKE_P0 P1_FAKE_ACCOUNT_CREDENTIAL=P1_FAKE_P1 NETRC=P1_FAKE_NETRC SSH_AUTH_SOCK=P1_FAKE_SOCK SSH_AGENT_PID=P1_FAKE_PID sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m tox -e py311-cover --skip-pkg-install -v --result-json dist/p1-repair/tox-result.json -- python -m pytest --cov --cov-report=term-missing --cov-report=xml:dist/p1-repair/coverage.xml --cov-report=json:dist/p1-repair/coverage.json --junitxml=dist/p1-repair/junit.xml -vv 2>&1 | tee dist/p1-repair/tox.log
```

退出 **0**，168 passed。真正的 tox commands_pre 在 pytest 清环境之前输出 `account environment isolated`；预装依赖、无 runtime 联网安装、默认根目录入口。

### 4.6 仓库外独立进程及不同文件顺序

工作目录 `/private/var/folders/0k/2wdc58817qj3v6mcyst_x6ww0000gn/T/opencode`：

```bash
set -o pipefail
sandbox-exec -p '(version 1)(allow default)(deny network*)' /Users/lld/emtl/.venv/bin/python -m pytest /Users/lld/emtl/tests/test_orders.py /Users/lld/emtl/tests/test_auth.py /Users/lld/emtl/tests/test_logging_safety.py /Users/lld/emtl/tests/test_core.py /Users/lld/emtl/tests/test_wrapper_contract.py /Users/lld/emtl/tests/test_api_contract.py /Users/lld/emtl/tests/test_cli.py /Users/lld/emtl/tests/test_fixtures.py /Users/lld/emtl/tests/test_offline_ci.py /Users/lld/emtl/tests/test_offline_guard.py /Users/lld/emtl/tests/test_test_safety.py -vv --junitxml=/Users/lld/emtl/dist/p1-repair/outside-junit.xml 2>&1 | tee /Users/lld/emtl/dist/p1-repair/outside.log
```

退出 **0**，168 passed。没有累计第一轮覆盖率。

另从 `/Users/lld/emtl` 验证显式目录入口（退出 **0**，168 passed）：

```bash
set -o pipefail
sandbox-exec -p '(version 1)(allow default)(deny network*)' .venv/bin/python -m pytest tests/ -q --junitxml=dist/p1-repair/explicit-junit.xml 2>&1 | tee dist/p1-repair/explicit.log
```

### 4.7 最终静态检查

工作目录 `/Users/lld/emtl`：

```bash
set -o pipefail
.venv/bin/ruff check --no-cache src/emtl tests conftest.py ci/check_offline_network.py ci/check_test_environment.py ci/run_offline_tests.py 2>&1 | tee dist/p1-repair/ruff.log
.venv/bin/black --check src/emtl tests conftest.py ci/check_offline_network.py ci/check_test_environment.py ci/run_offline_tests.py 2>&1 | tee dist/p1-repair/black.log
git diff --check
git diff --cached --check
git diff -- src/emtl
```

最终 Ruff、Black 与 diff 检查退出 **0**；生产源码 diff 为空。初次 lint 发现新增测试的 lambda 赋值及列表拼接风格、Black 排版问题，已只修复测试/CI 文件后重验。

## 5. 覆盖率比较与原始报告

| 数据 | 行 | 分支 | 合并计分 |
| --- | --- | --- | --- |
| P0 历史实测（41 项） | 169/191 | 26/40 | 84.42% |
| 修复前 P1 历史实测（91 项） | 169/191 | 27/40 | 84.85% |
| 本次 macOS tox（168 项） | 169/191 | 35/40 | 88.31% |

原历史 JSON 来自本机 `/private/var/folders/0k/2wdc58817qj3v6mcyst_x6ww0000gn/T/opencode/p1-baseline.json`、`p1-after.json`，本轮分别复制保留为 `dist/p1-repair/p0-baseline-coverage.json`、`before-repair-coverage.json`；不是本轮重新跑出的历史 suite。

本轮 `coverage.json`/`coverage.xml`、`junit.xml`、`tox-result.json` 与 `tox.log` 均由 §4.5 实际生成。`core.py` 当前 125 条语句/32 个分支全覆盖；仍不声称离线样本证明线上协议、资金结果或 P2 并发安全。剩余遗漏位于 CLI 子进程、生成版本文件和非本次风险范围的 utils 等路径。

## 6. 剩余风险及远端验收操作

1. GitHub Actions 尚未执行，远端 artifacts 链接不存在。维护者批准后提交/推送当前分支，创建面向 master 的 PR，等待新离线 workflow 以及原必需 workflow；本次不会自动执行这些操作。
2. 检查 artifact `offline-test-evidence` 内 `network-mode.txt=NetworkMode=none`、OS 探针日志、`container-exit-code.txt=0`、`host-status.txt` 各状态、三套 JUnit、coverage、versions/commands/synthetic-environment JSON，并将真实 run/artifact URL 追加本文。
3. 独立 Review 需审查全部 tracked/staged/untracked；任何缺报告、重复提交、兼容性变化或禁网证据缺失均不能 PASS。先前 Review FAIL 不能由本 Build 自行改称 PASS。
4. 已有全局 Session/token、登录不检查业务状态和无匹配保留旧 token、裸 raise、OCR 递归未改；这些不是本次新引入的问题，后续修复需授权。订单异常始终可能代表“结果未知”，不能自动重发。
5. 假响应/错误码均人工合成，真实券商完整 schema 仍未知。Python guard 不是任意程序沙箱；Docker none 仍允许容器内部 loopback。

## 7. 本地 Docker 实际执行记录

当前环境已可响应 Docker daemon（`docker info --format '{{.ServerVersion}}'` 退出 0，29.5.2），不同于上一轮没有 Docker 的环境。

本轮已启动实际命令，工作目录 `/Users/lld/emtl`：

```bash
docker build --file ci/offline.Dockerfile --tag emtl-p1-offline:repair .
```

stdout/stderr 保存至 `dist/p1-repair/docker-build.log`，真实命令、cwd、退出码由包装进程保存至 `docker-build-result.json`。结果待命令完成后追加；在此之前不宣称镜像构建或 Linux 禁网测试通过。

## 8. 本地 Linux 验证（历史结果补记）

本节追加已经完成的构建和上一轮 Review 的 Linux 运行结果。第 1–7 节保留其原有时间点的记录；第 7 节“待命令完成”现已由下列真实结果补齐，未覆盖或删除旧证据。**这不是最终提交的远端 CI 验收，P1 总体仍为 NEEDS EVIDENCE。**

### 8.1 镜像、基线及版本来源

- 构建、历史运行及本次文档更新对应的仓库 HEAD 均为 `2d8929b6b3df88131419e89b868a4cdb0b81c7a3`，分支 `refactor/p1-offline-tests`。实现仍含未提交/未跟踪内容，不能声称该 HEAD 已包含全部实现。
- 镜像标签：`emtl-p1-offline:repair`。
- 镜像 ID：`sha256:09508f8f6fc8819496d815cad28e5fe18963ce4635aad23beef3c537861ceb1e`；平台：`linux/amd64`，本次只读 inspect 再次确认。
- 基础镜像构建日志记录的 digest：`sha256:a78ac56989e704fadc8e9be30b3fe78e7bf8a52572a726911e525c30468604f8`；不是 emtl 镜像 ID，两者不能混用。
- Linux Python **3.11.18**、pytest **9.2.0**、pytest-cov **7.1.0**、coverage **7.17.2**，直接取自已存在 Linux 运行日志第 5 行的版本 JSON；tox **4.67.12** 取自同一镜像的构建日志 `Successfully installed ... tox-4.67.12`。未根据当前宿主安装或镜像标签猜测版本。
- Ruff **0.4.1**、Black **24.4.0** 的既有通过记录属于 macOS（§3、§4.7），不冒称在 Linux 容器运行过这些检查。

### 8.2 已执行的真实命令和结果

宿主工作目录 `/Users/lld/emtl`，以下为历史实际执行命令，本次文档更新没有重新构建或重跑测试：

```bash
docker build --file ci/offline.Dockerfile --tag emtl-p1-offline:repair .
docker run --rm --network none emtl-p1-offline:repair
```

构建退出码 **0**（原始 `dist/p1-repair/docker-build-result.json`）；运行退出码 **0**（上一轮 Review 工具结果及本次用户提供的已知证据）。运行日志保留完整控制台输出。该次运行无宿主目录挂载、无 `-e` 凭证注入，镜像 CMD 执行 `python ci/run_offline_tests.py`。

| 容器内步骤 | 工作目录 | 实际退出码 | 结果/日志依据 |
| --- | --- | --- | --- |
| `/usr/local/bin/python ci/check_offline_network.py` | `/workspace` | 0 | `OS network namespace isolation verified`；独立于 pytest/Python Mock |
| 版本查询 | `/workspace` | 0 | Python/pytest/pytest-cov/coverage 版本 JSON |
| 完整 tox、凭证检查、默认 pytest 入口 | `/workspace` | 0 | `account environment isolated`，168 passed；生成覆盖率/JUnit |
| 仓库外、不同文件顺序完整 pytest | `/tmp`（容器内） | 0 | 168 passed |
| 显式 `tests/` 完整 pytest | `/workspace` | 0 | 168 passed |

三次完整测试不是累计 504 项不同用例，而是同一 168 项套件的三种入口/顺序验证。原始完整命令均保存在稳定日志的 `RUN` 行；主要测试命令如下：

```bash
# /workspace；启动 tox 的父进程使用下方明确合成的环境设置。
/usr/local/bin/python -m tox -e py311-cover --skip-pkg-install -v --result-json /workspace/dist/p1-offline/tox-result.json -- python -m pytest --cov --cov-report=term-missing --cov-report=xml:/workspace/dist/p1-offline/coverage.xml --cov-report=json:/workspace/dist/p1-offline/coverage.json --junitxml=/workspace/dist/p1-offline/junit.xml -vv

# /tmp（容器内）
/workspace/.tox/py311-cover/bin/python -m pytest -vv --junitxml=/workspace/dist/p1-offline/outside-junit.xml /workspace/tests/test_orders.py /workspace/tests/test_auth.py /workspace/tests/test_logging_safety.py /workspace/tests/test_core.py /workspace/tests/test_api_contract.py /workspace/tests/test_cli.py /workspace/tests/test_fixtures.py /workspace/tests/test_offline_ci.py /workspace/tests/test_offline_guard.py /workspace/tests/test_test_safety.py /workspace/tests/test_wrapper_contract.py

# /workspace
/workspace/.tox/py311-cover/bin/python -m pytest tests/ -q --junitxml=/workspace/dist/p1-offline/explicit-junit.xml
```

驱动构造的合成父进程环境（值均为 `P1_FAKE_VALUE`）：`EM_USERNAME`、`EM_PASSWORD`、`EM_P1_SENTINEL`、`P0_FAKE_ACCOUNT_CREDENTIAL`、`P1_FAKE_ACCOUNT_CREDENTIAL`、`NETRC`、`SSH_AUTH_SOCK`、`SSH_AGENT_PID`；另设 `PIP_NO_INDEX=1`、`PIP_DISABLE_PIP_VERSION_CHECK=1`。tox precheck 在 pytest 清账户环境前通过。这不是真实凭证配置。

Linux 控制台覆盖率为 **88.31%**（行/分支合并计分），`core.py` 为 125 条语句、32 个分支、100.00%。既有 macOS 原始 JSON 明确给出整体行 169/191、分支 35/40；不将 macOS JSON 当作已经取回的 Linux JSON。已知行情吞异常变异的两个预期失败仍由 §4.4 的历史日志/JUnit 证明，未在此次 Linux 运行中再次注入变异。

### 8.3 当前工作区与构建快照的差异

本次文档核对在 `/Users/lld/emtl` 执行以下只读命令，均退出 0；inspect 返回上述完整镜像 ID 和平台，生产源码 diff 为空：

```bash
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --name-only HEAD -- src/emtl
docker image inspect --format '{{.Id}} {{.Os}}/{{.Architecture}}' emtl-p1-offline:repair
```

本次用固定镜像 ID 在 `--network none` 短生命周期容器中只读提取文件并与宿主比较，未运行 emtl/OCR，也未修改镜像或测试文件：

- 比较 `src/emtl`（排除构建生成的 `_version.py`）、`tests`、`ci` 下的 Python 文件，所有 `.github/workflows/*.yml`，以及 `.dockerignore`、`.coveragerc`、根 `conftest.py`、tox/pytest/setup/pyproject、Dockerfile，共 **37 个文件**。
- **36 个相同**；唯一不同为 `tests/test_wrapper_contract.py:12–13`：

```diff
-WRAPPERS = QUERY_CALLS + [
+WRAPPERS = [
+    *QUERY_CALLS,
```

两种写法对这里的列表产生相同包装层用例，是风格修改，不是交易行为变化。镜像文件 SHA256 为 `3e848a99d1b99ac63039e6b1b618dfaf586787517ddec407e3f9358b4e4640f1`，当前文件为 `fa2a48a0af6d59033d81ccf08b00f1d3bd544f46eb631f307974059d86acf15d`。这仍意味着镜像不等同于最终工作区快照；报告和证据文档也是构建后的补记，不在上述代码/config 比较范围中。

文档更新开始时 Git 状态为 6 个已跟踪修改、17 个未跟踪文件、无 staged 改动；均为既有 P1 工作。本次不撤销或提交这些内容。`git diff --name-only HEAD -- src/emtl` 输出为空。本次只追加验收报告和证据文档，不改变已有生产、测试或 CI 文件。

### 8.4 稳定证据与仍缺失的原始文件

已审查的日志不含真实账户、Cookie/token 值或交易响应；其中账户及错误值仅为合成样本。归档到 [`evidence/P1-local-linux/`](evidence/P1-local-linux/README.md)：

- `build-output.txt`：历史实际构建日志副本；仅将一处终端 `\r\r\n` 换行序列规范化为 LF 以避免文档空白检查错误，原始日志不变，来源与归档 SHA256 分别记录。
- `docker-build-result.json`：历史构建命令、cwd、退出码的逐字节副本。
- `linux-run-output.txt`：从本会话已存在的 shell 输出恢复的历史 Linux 控制台日志，含版本、完整命令、OS 探针、凭证隔离、三轮测试结果及退出码；不是本次新跑的结果。
- `README.md`：来源、SHA256、核查范围和证据限制。

原容器由 `--rm` 自动删除；其 `/workspace/dist/p1-offline/` 中 Linux JUnit、coverage XML/JSON、tox-result、versions/commands JSON **未导出到宿主，现无原始文件可归档**。不能仅凭控制台的“生成文件”文本声称已保存这些原始报告，也不重建/伪造报告补缺。宿主 `dist/p1-repair/` 的同名 XML/JSON 是既有 macOS 结果。

### 8.5 远端验收：待完成

- [ ] 对最终提交在干净 GitHub Actions runner 上完成镜像构建及整套系统禁网运行。
- [ ] 保存 runner 实际 `docker inspect` 的 `NetworkMode=none` 证据；本次历史 `docker run --rm --network none` 没有留下已删除容器的 inspect 文件，不冒称已完成该 runner 步骤。
- [ ] 核验远端实际报告复制、失败状态保留、容器清理和 artifacts 上传。
- [ ] 保存 Linux 原始 JUnit、coverage、tox、版本/命令/环境和日志 artifacts，并追加真实 run/artifact URL（当前无链接）。
- [ ] 将最终提交的远端结果交独立 Review；当前 Review 结论仍为 **NEEDS EVIDENCE**，不是 PASS。

本次仅补记历史验证，不 commit、push、merge，不执行发布或触发远端 CI。
