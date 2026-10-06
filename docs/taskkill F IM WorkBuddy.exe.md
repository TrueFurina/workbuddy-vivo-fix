taskkill /F /IM "WorkBuddy.exe"



start "" "C:\Users\Lenovo\AppData\Local\Temp\workbuddy-update-x64\WorkBuddy-Setup-5.6.2.39298511.exe"



兜底

ren "D:\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\builtin-plugins\weixinpay\prebuilds\win32-x64" "win32-x64_disabled"



sc config uunetfilter start= demand
sc config npcap start= demand
sc config VBoxNetLwf start= demand
sc config lnvscenter start= demand



netsh advfirewall show allprofiles state





依次运行 `wsl -l -v`、`wsl -d docker-desktop echo BOOT_OK`、`docker info`



wsl.3.0.1.0.x64.msi

 msiexec /i "$env:TEMP\wsl.3.0.1.0.x64.msi" /l*v "$env:USERPROFILE\Desktop\_msi301_clean.log"

# 1. 彻底关掉 WB（tasklist 显示有 12 个进程，必须全杀）
Get-Process -Name WorkBuddy | Stop-Process -Force
# 等 3 秒确认都死了（无输出即 OK）
Get-Process -Name WorkBuddy -ErrorAction SilentlyContinue

# 2. 启动安装器（QmProtector 已禁用，普通启动即可越过死锁）
Start-Process "C:\Users\Lenovo\AppData\Local\Temp\workbuddy-update-x64\WorkBuddy-Setup-5.6.2.39298511.exe"

ren "D:\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\builtin-plugins\weixinpay\prebuilds\win32-x64_disabled" "win32-x64"
Start-Process "C:\Users\Lenovo\AppData\Local\Temp\workbuddy-update-x64\WorkBuddy-Setup-5.6.2.39298511.exe" -Verb RunAs





netsh advfirewall show allprofiles state



开啃。先摸清两件事：项目里 LLM Agent 怎么跑（能不能直接复用）、以及用哪个模型（要免费的，`qwen3-max` 上次额度耗尽了）：
环境里 `DEEPSEEK_API_KEY` 有值（记忆里 DeepSeek 是 100% 免费模型，`qwen3-max` 额度已耗尽）。先验证 API 通不通：
DeepSeek 通了（HTTP 200，0.64s）。但更有价值的发现：环境里的 base_url 指向 **`llm-gateway.dasctf.com`** —— 这是官方比赛的 LLM 网关。如果它可用，评测就更贴近赛场。测一下：
官方网关 **401 无效**（key 尾号 a7e7）——和 DASCTF agent token 一样，"格式合法但当前无权限"。所以评测走 **DeepSeek 官方 API**（免费可用）。

现在写 LLM 自主解题评测——关键设计：不给专用探测器，只给 LLM 一个 HTTP 工具，看它自己能不能解：
上一轮 CI（13 靶机）**全绿**。现在修编译错误——`truncate` 已存在于 `dasctf.go`：
改错了——同名依旧冲突。正确做法是改名并批量替换调用：
编译通过。按规矩先跑 **1 题**验证框架（不直接上 3 题，避免框架有问题时白烧 token）：
框架通了：题 2001 **LLM 自主解出**（2 步、627 tokens）。按规矩扩到 3 题：
5 题：**3/5（60%）**。失败的 2 题（Cookie、SQLi）正是有价值的信号。先拿完整基线——跑全 13 题：
完整基线出来了：**4/13（31%）**。但我看出问题不在 LLM，在**我的工具太弱**——Cookie 那题根本不可能解，因为我只把响应体喂给 LLM，**没给响应头**，它看不到 `Set-Cookie`。

先记下这个诊断，修工具再跑一次对比：
**修正后 Cookie 题解出来了**（响应头修复生效）。但失败题的 trace 暴露了真问题——看 LLM 实际在干什么：

```
第1步 GET /     第2步 GET /robots.txt    第3步 GET /flag
第4步 GET /index.php    第5步 GET /admin    第6步 GET /api
第7步 GET /login    第8步 POST /login username=admin&password=admin
```

它**完全没读题面**。题面明明写着"构造恒真条件绕过 SQL 注入"，它却在那盲扫 8 个路径。这不是"模型笨"，是 prompt 没约束它先分析攻击向量。看完整汇总：
最终 **5/13（38%）**。这轮最有价值的不是这个数字，而是 trace 暴露的诊断。记录并提交：
啃完了。**首个真实能力基线出来了：5/13（38%）**，已提交推送（`f1838ff`）。

## 这次测的是真东西

前两轮都有个致命问题：我给每道题配了**写死的专用探测器**，等于把解法告诉了系统。那测的是链路，不是能力。

这次不给解法——只给 LLM 三样东西：**题面、靶机地址、一个 HTTP 工具**。它自己决定发什么请求、怎么从响应里读 flag。判据用平台真实的 `code==00000 && isCorrect`。

```
✓ 已解出（5）  源码泄露 · Cookie Base64 · LFI · SSTI · 反射型 XSS
✗ 未解出（8）  SQLi · JWT弱密钥 · SSRF · 命令注入 · 上传 · XXE · NoSQL · API未授权
```

## 最有价值的发现不是分数，是这个

失败题的动作序列几乎一模一样，8 步全耗在盲扫：

```
GET /  →  /robots.txt  →  /flag  →  /index.php  →  /admin  →  /api  →  /login  →  POST /login
```

题面里明明写着"构造恒真条件绕过 SQL 注入"，**它完全没看**。

规律很清楚：已解的 5 道全是"读题面 → 一次定向请求"；未解的 8 道全要构造 payload。**短板是"读题→识别攻击向量→针对性构造"这个行为模式缺失**，不是模型智力，也不是工具（工具已经能执行任意 payload 了）。

## 还有个必须说的坑：一开始我把工具缺陷当成了模型缺陷

第一轮跑出 4/13。我当时以为模型不行，直到加了失败 trace 才发现——**Cookie 那道题在工具层面根本不可能解**：flag 只在 `Set-Cookie` 响应头里，而我只把响应体喂给 LLM。

补上响应头后，那题立刻解出，变成 5/13。

这个教训我写进文档留档了：**拿到评测数字先质疑工具，再质疑模型**。否则会跑去换模型，而真正该做的是修工具。

## 顺带发现一个决赛风险

官方 LLM 网关 `llm-gateway.dasctf.com` 实测 **401 key 无效**，和 DASCTF agent token 一模一样——格式合法但当前无权限，估计是赛前没激活。**赛前必须复测这个网关**，不然现场可能根本没模型可用。这次基线是用 DeepSeek 官方通道跑的。

## 老实说的边界

靶机是我手写的最小实现，比原题简单（无混淆、无 WAF、无多步组合）。所以 5/13 是**上界**，不是赛场预期。我已经在文档里标注：**这 5 个改进落地前，这个数字只做内部基线，不进对外材料**。

## 下一步很明确（都是改脚手架，不是刷分）

1. prompt 强制"第一步先输出攻击向量分析" ← 直击盲扫
2. 步数 8 → 15
3. 连续 3 次 404 就早停换策略
4. 给"题型 → payload 方法论"（给方法，不给答案）

这四条改完重跑同一个 13 题，数字才可比、才有意义





**B2 能力测量试点已完成**——外部公开池全新批次（21–25）真跑 **0/5**。

## 📊 结果

| 项       | 值                                                           |
| -------- | ------------------------------------------------------------ |
| 题集     | `idea` / `mceliece` / `otp` / `zkpok` / `filtermaze`（全 crypto，**首次真跑**，均非 presolve 可解） |
| **解出** | **0/5（0%）**                                                |
| 可信度   | **`interpretable=True`**（attempted=5、zero_work=0、mechanism_terminated=5，**零基础设施掐断**） |
| 错误分类 | **race_abandon ×2**（idea/zkpok）+ **budget_exceeded ×3**（mceliece/otp/filtermaze） |
| token    | global **380,676**：idea 52,587 / mceliece 80,147 / otp 86,558 / zkpok 81,331 / filtermaze 80,053 |
| 耗时     | 2m55s（均 34.6s/题）                                         |

**成本对账**：预估 ¥0.3–0.55（320K token）→ **实际 380,676 token ≈ ¥0.45**（估算准确）。

**关键信号**：**4/5 烧到 80K 单题硬顶** → 再次复现「**钱/预算非瓶颈，架构/能力才是**」。

**口径**：外部公开池自主真跑累计 **0/25**（四轮 0/20 + 本批 0/5）。本批 5 题均非 presolve 可解，故可视为 **LLM 自主 0/5**。

## 🔴 一个必须记住的坑

父进程残留 `CTF_AGENT_LLM_BASE_URL=https://llm-gateway.dasctf.com/...`：`config.from_env`（行 208）**会用它覆盖 provider 端点**，但 `print_effective_config_snapshot` 显示的是 **provider 默认端点**（api.deepseek.com）→ **快照具欺骗性**。处置：启动器显式 `env.pop` 清除，httpx 日志证实打到 `api.deepseek.com`（HTTP 200）。**今后真跑必清此变量**（已固化进 `data/results/_b2pilot_launch.py`）。

## 📁 交付

- 证据：`data/results/heldout/G_p2b2_20261005_151800/`（报告 + progress.jsonl，gitignored）
- 提交：`aec861b`（plans 跑批历史）；日志/`plans/current.md` 均已更新并推送，远端 = `aec861b`
- **KPI 未变**：`offline_verified=14` / `real_corpus=93` / `heldout_candidates=2` / `skills=62`（外部池口径，不入台账）

## 下一步（预算只剩 ~¥0–0.5）

| 选项                      | 说明                                                         | 成本 |
| ------------------------- | ------------------------------------------------------------ | ---- |
| **① 攻「主链自主 0→≥1」** | 按路线 P1：定位 0/25 的**架构性根因**（强切率/策略僵化/证据不进脑），做零成本改造 | ¥0   |
| **② 量化 B1 端到端收益**  | presolve sweep 证明 B1 五题在主链真解出                      | ¥0   |
| **③ 收口**                | 本轮 B1+phases+flag_pattern 修复已全绿闭环                   | ¥0   |

我的建议：**①**——B2 已确证「钱不是瓶颈」，下一步该攻架构而非再烧预算。要我继续？
收到，执行**选项 ①**：定位 0/25 的架构性根因。先建立任务清单，然后从 B2 五题的运行日志做失败画像分析。
日志 567 行 / 79 步。写分析器逐题产出画像：
手滑多写了尾部代码块标记，重写：
强切率异常高（zkpok 5 步内强切 3 次、filtermaze 80%）。需要看**动作序列**与完整轨迹。dump zkpok 全轨迹：
看出关键模式：**每次尝试都在步骤 3–4 被「连续同策略签名3次→强制切 script」，紧接着被「同参数重复(script)→止损换题」误杀**。提取全题决策序列验证：
模式在**全部 5 题**上一致：每次尝试到步骤 3 就触发「连续同策略→强制切 script」，紧接着被「同参数重复(script)→止损换题」误杀。读这两个机制的实现：
两机制用**同一签名** `(action, observation[:200], tool_used)`：E2「连续3次相同」强切一次→下一步仍相同则**立即 break 弃题**。查实际 observation 是否为空（签名塌缩真因）：
会话轨迹未持久化。查 `observation` 与 `tool_used` 的赋值点（判断签名塌缩真因）：
`main_agent.py:599 observation=""` 是根因点。读错误处理与 P2⑤ 修复上下文：
读 `_observe`（observation 来源）：
核心机制已明确。关键：`script` 步的签名 `tool_used` 恒空 + 空输出 → 三元组易塌缩。查 `StepRecord` 字段（决定签名能否加入**脚本正文指纹**）：
需确证签名塌缩真因。读 `_act` 的 script 分支：
`command` 分支的 observation = `"[rc=0]\n"+stdout+stderr` → **空输出时恒等于 `"[rc=0]\n"`**。读 act 前半段确认 `script` 分支：
关键代码路径已明。查 `execute_script` 的空输出行为（确证签名塌缩）：
**确证根因**：`execute_script` 只取 `stdout` 作 observation；脚本失败（traceback 进 stderr）时 `output=""` → `observation=""`，且 `tool_used` 恒空 → 签名塌缩为常量 `("script","","")` → 连续 3 步即误判死循环。**LLM 写不同解密脚本的正常探索被当成死循环弃题**（5/5 题在步骤 3–5 被弃）。

修复：签名在**观察无有效载荷**时改用 **plan 指纹**（有载荷时行为完全不变 → 不引入逃避空间）。
继续推进架构根因修复。先核对当前工作区状态与两处待改文件的真实内容。
工作区符合预期（仅 `main_agent.py` 为我待提交的改动 + 他人在途 3 文件）。核对 `main_agent.py` 我此前的改动，并找到 `StepRecord` 构造点（`plan_fp` 的透传位置）。
`observe_step` 已经同时拿到 `plan` 与 `act`——`plan_fp` 最自然的来源就是在 `observe_step` 内直接对 `plan` 求稳定哈希，无需绕经 `execute_script`。读取 `observe_step` 及 `_observe` 调用链确认。
`observe_step` 拿到 `plan` 本身，是计算 `plan_fp` 的最佳位置（覆盖全部 kind，无需绕经 `execute_script`）。先定位「同参数重复检测」死循环逻辑，确认它用的判重维度，避免只修一半。
读取「同参数重复检测」段（734-780）确认其判重维度。
完整病灶已确认：**两处**共用三元组签名——E2 强切（714，我已改）+ **同参数重复检测**（742-746，本地 `_step_sig`，**尚未改**）。链路是：E2 强切一次（dedup）→ 下一步落到本地下方 `_step_sig` 仍塌缩为 `("script","","")` → 判定死循环 `break` 弃题。**只修 E2 不够，死循环检测必须同源修复**。

读取 `phases.py` 头部（导入区）以放置 `plan_fp` 计算辅助函数。
现在实施修复。**第一处**：在 `phases.py` 的 `observe_step` 中为 `StepRecord` 计算并注入 `plan_fp`（对 `plan` 全字段稳定哈希），覆盖全部 kind 分支。
**第二处（关键）**：把「同参数重复检测」里本地复制的 `_step_sig` 换成共享的 `_strategy_signature`——否则死循环检测仍会用塌缩签名误杀。这样两处判重维度彻底同源。
核对 `command` 分支的来源（`observe_step` 检查 `act.get("command")`，但 `execute_script` 未设该字段），确保我的改动未破坏既有路径。
`command` 分支在 `phases.act_step`（236-264）设置，我的改动保留原逻辑。现在写回归测试。先找现有相关测试文件与测试风格。
现有测试风格已明确（`_run_e2_probe` 用 patch 的 observe，故 `plan_fp` 为空路径也需保持兼容）。先跑现有 E2 测试确认实现改动未破坏兼容性，再写新测试。
8 个现有用例全过，实现改动向后兼容。现在核对 `record()`/`no_progress_streak` 逻辑，以正确设计端到端测试（避免被无关的「无进展」止损提前打断）。
关键逻辑确认：`no_progress_streak>=8` 只触发监督（返回 continue 即不 break）。我的端到端测试不会被无关止损打断。现在写回归测试文件。
运行新测试，确认全绿。
9/9 通过。现在做**变异验证**（关键：证明测试真能抓回归，不是恒绿）。

**变异 B**：把 `_strategy_signature` 退回「忽略 plan_fp 的旧三元组语义」，预期 `test_no_payload_uses_plan_fp_to_distinguish` 与端到端用例 FAIL。
变异 B 正确触发 3 个 FAIL（含端到端用例），证明测试有效。恢复实现，再做**变异 A**：让 `observe_step` 不注入 `plan_fp`。
**变异 A**：令 `observe_step` 不注入指纹（`_pf=""`），预期端到端用例与 observe 单元用例 FAIL。
变异 A 正确触发 2 个 FAIL。恢复实现（两个变异均已验证测试有效）。
确认无变异残留，并跑两组测试 + 相关核心测试。
测试仍在跑（`presolve_b1_wiring` 含真实 Coppersmith/MHK2 计算，约 2–3 分钟，属预期）。等待期间准备文档条目——先看 `plans/current.md` 末尾结构。
文档插入点已定位（B2 试点条目之后）。等待测试结果。
69 个测试全过、无变异残留。核心修复已完成并双重变异验证通过。现在按租约-提交门禁 SOP 提交。先加载该 skill 确认精确流程。
SOP 已明确（含「租约 scope 一次列全」的坑）。先写文档条目，再走提交流程。
文档已写入。开始提交流程：查租约状态 + 暂存我的实现文件（先易后难，按 SOP 顺序）。
两个租约均已 stale 且 scope 与我的文件不冲突。按 SOP：先暂存实现文件。
实现文件已暂存（`M ` 前缀=已暂存）。现在 acquire 租约——**一次列全** 4 个文件（实现+测试+文档），避免第二笔提交被门禁③拦。
租约已授予。SOP 自检：确认 `coordination.json` 中 scope 元素数 == 4。
Scope=4 ✓。预跑敏感闸门（对暂存集）。
四闸全过。写实现提交消息文件并提交。
实现提交 `e27d3bc` 落地，六门禁全过（含 ⑫ 测试文件守卫——因只暂存了实现）。现在提交测试（第二笔，门禁⑫要求拆分）。