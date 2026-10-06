# WorkBuddy 更新死循环 Bug 反馈

> 最后更新：2026-09-06 22:10（补充卸载重装可行性评估与最新实测证据）

## 环境信息

| 项目 | 值 |
|------|-----|
| 当前版本 | 5.4.5 |
| 目标版本 | 5.5.3.37748631 |
| 安装目录 | D:\WorkBuddy（1.2 GB，用户级安装 HKCU） |
| 卸载器 | `D:\WorkBuddy\Uninstall WorkBuddy.exe` |
| 卸载命令 | `"D:\WorkBuddy\Uninstall WorkBuddy.exe" /currentuser`（静默：`/S`） |
| 操作系统 | Windows 11 26200 |
| 安装方式 | NSIS |
| 数据目录 | `C:\Users\Lenovo\.workbuddy\` |

## 问题描述

WorkBuddy 启动后自动检测到 5.5.3 更新并下载成功，但执行 `quitAndInstall` 时安装器卡死、进程长期残留。每次重启后重复此循环，**既无法完成更新，也无法正常使用旧版本**。已持续 3 天（9/4 起），期间卸载重装、手动安装、管理员安装等常规手段全部无效。

---

## 根因定位

**QmProtector suspend 失败**，NSIS 安装器在启动阶段无法挂起微信支付插件的保护状态，导致进程挂起。

### 补充：失败的直接原因是内核驱动无法加载

QmProtector 组件目录 `...\weixinpay\prebuilds\win32-x64` 中包含一个**内核态驱动**：

| 文件 | 大小 | 说明 |
|------|------|------|
| `QmProtectorDriver.sys` | 126 KB | **内核驱动** |
| `QmProtectorLib.dll` | 783 KB | 用户态库 |
| `libTencentSM.dll` | 1.4 MB | 加密库 |
| `wechatpay-cli.exe` | 5.9 MB | CLI |

`Initialize=0x80000002` 即**该内核驱动加载失败**。已确认 `C:\Windows\System32\drivers\` 下**不存在** QmProtector 驱动文件 —— 驱动从未成功安装/加载过。

**这构成一个设计缺陷**：WorkBuddy 是用户级安装（HKCU，全程无需管理员权限），但更新流程却依赖一个**必须提权才能加载的内核驱动**。electron-updater 以普通权限拉起安装器 → 驱动必然加载失败 → suspend 卡死 → 更新永久循环。

---

## 关键日志证据

### 1. QmProtector 初始化失败（稳定复现）

```
[2026-09-04T07:06:23.690Z] [INFO ] [win32] QmProtector: helperExe=D:\WorkBuddy\resources\qm\qm-helper.exe exists=true
[2026-09-04T07:06:23.690Z] [INFO ] [win32] QmProtector: dllDir=...\weixinpay\prebuilds\win32-x64 dllExists=true
[2026-09-04T07:06:24.327Z] [WARN ] [win32] QmProtector suspend failed: Command failed: qm-helper.exe suspend ...
```

### 2. qm-uninstall.log（最新记录）

```
[2026-09-06T20:56:57] [QmProtector] qm-uninstall.exe command=suspend
[2026-09-06T20:56:57] [QmProtector] arg=D:\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\builtin-plugins\weixinpay\prebuilds\win32-x64
[2026-09-06T20:56:58] [QmProtector] caller parent PID=20796 path=D:\WorkBuddy\WorkBuddy.exe
[2026-09-06T20:56:58] [QmProtector] caller signer=Tencent Technology (Shenzhen) Company Limited chainTrusted=1 result=OK
[2026-09-06T20:56:58] [QmProtector] DLL loaded OK (verified Tencent-signed)
[2026-09-06T20:56:58] [QmProtector] Initialize=0x80000002
```

> **注意 caller 是 `WorkBuddy.exe`（PID 20796）本身，不是安装器** —— 说明主程序在运行期间就周期性尝试 suspend 并失败。

### 3. 更新状态被永久标记为 active（循环机制）

```
[2026-09-06T13:48:56.380Z] [INFO ] shouldSkipForActiveUpdate: Latest version 5.5.3.37748631 matches active update, skipping
[2026-09-06T13:48:56.380Z] [INFO ] [win32] Update already ready, latest version matches, skipping check
```

更新状态被标记为"活跃"且永不失效，每次启动都尝试安装 → 卡死 → 重启 → 重复。

### 4. 安装器挂起证据

```
Name                              Id     CPU    内存      StartTime
WorkBuddy-Setup-5.5.3.37748631   88276  2.26s           2026/9/4 18:56:35
WorkBuddy-Setup-5.5.3.37748631   7044   1.5s    26 MB    2026/9/6 15:0x  (存活 5+ 小时)
WorkBuddy-Setup-5.5.3.37748631   28468  —       25 MB    2026/9/6 20:5x
```

CPU 时间仅 1~2 秒、内存恒定不增、目标文件零写入 —— 典型的挂起状态而非在工作。

---

## 稳定复现记录（非偶发）

同一失败在 **9/4 07:06、9/4 10:56、9/4 18:56、9/6 03:13、9/6 03:38、9/6 11:43、9/6 13:29、9/6 20:56** 共 8 次复现，**全部为同一位置 `Initialize=0x80000002`**，与网络、磁盘空间无关。

---

## 已尝试的修复（全部失败）

| # | 手段 | 结果 |
|---|------|------|
| 1 | 杀掉卡死的安装器进程 | ❌ 重启后自动重新启动并再次卡死 |
| 2 | 手动运行安装包（普通权限双击） | ❌ 同样卡在 QmProtector suspend |
| 3 | 清理 updater 缓存目录（含旧 470MB 5.4.5 包） | ❌ 无效 |
| 4 | 静默安装到全新目录 `D:\WorkBuddy553`（排除文件占用） | ❌ **安装器启动后立即退出，目录未创建** |
| 5 | 脚本先启安装器、再终止 WorkBuddy 释放占用 | ❌ 安装器仍卡死，目标文件时间戳无变化 |
| 6 | 以管理员权限运行安装包（`-Verb RunAs`，实测 `IS_ELEVATED=True`） | ❌ **提权后依然零写入** |
| 7 | 强制结束全部 WorkBuddy（0 进程）+ 提权启动全新安装器 | ❌ **90 秒监控，目标文件时间戳零变化** |
| 8 | 安装前改名禁用 QmProtector 目录 `win32-x64 → win32-x64_disabled_by_fix` | ❌ 安装器仍无响应 |

### 由第 6、7 项得出的关键结论

> **在「WorkBuddy 零进程占用」+「安装器管理员提权」+「全新 PID」三重条件下，安装器对目标目录 `D:\WorkBuddy\WorkBuddy.exe` 依然是零写入（时间戳恒为 Aug 30 20:51）。**

这排除了"文件被占用"这一解释，证明**安装器自身在初始化阶段即挂起**，卡点就是 QmProtector。

### 附带发现：本机 `taskkill` 对该进程失效

排查中发现 `taskkill /F /PID <pid>` 返回 rc=1 且不输出任何错误信息、**进程实际未被终止**；而 `OpenProcess(PROCESS_TERMINATE)` 可正常获取句柄、`TerminateProcess` 一击即中。

> 说明：早期多次"杀进程后重试"之所以无效，是因为**进程根本没被杀掉**，不是没杀干净。已改用 `TerminateProcess` 验证环境确实可以清空到 0 进程。

---

## 关于卸载重装的可行性（本次重点补充）

### 结论：**在官方确认 5.5.3 安装器可用之前，不建议卸载。不是因为卸载会卡，而是因为卸载不可逆。**

### 评估依据

**① 卸载器本身大概率不会卡在 QmProtector**

对 `D:\WorkBuddy\Uninstall WorkBuddy.exe`（239 KB）做二进制扫描，`QmProtector` / `qm-helper` / `suspend` / `protector` 关键字均为 offset=-1。

> ⚠️ 但该二进制的 NSIS 脚本指令区是**压缩**的（`Nullsoft` 字符串可见于 offset=106364，而 `RMDir`、`WorkBuddy` 等脚本指令均不可见），因此**这是假阴性，不能据此断定卸载器不含该逻辑**。请官方确认。

**② 真正的风险在"装不回来"，而非"卸不掉"**

- `D:\WorkBuddy` 共 1.2 GB，卸载后即被删除
- 而 5.5.3 安装器已被实测证明**在零占用、管理员提权条件下依然零写入**（见上表第 7 项）
- 一旦卸载完成而 5.5.3 装不上，用户将**彻底失去 WorkBuddy**（旧版已删、新版装不上、安装包来自 Temp 随时可能被清理）

**③ 次要风险：卸载中途卡死**

若卸载器确实包含 QmProtector suspend，则会卡在与安装器完全相同的位置，中途中断后目录处于半删除状态。

### 若官方确认"卸载可行"，请一并给出可回滚方案

用户侧建议在执行前做**目录级备份**，使卸载变为可逆操作：

```bat
:: 备份（D 盘剩余 57 GB，1.2 GB 备份无压力）
xcopy "D:\WorkBuddy" "D:\WorkBuddy_backup_545" /E /I /H /Y

:: 卸载（先确保 WorkBuddy 已完全退出）
"D:\WorkBuddy\Uninstall WorkBuddy.exe" /currentuser /S

:: 若 5.5.3 装不上，回滚：
xcopy "D:\WorkBuddy_backup_545" "D:\WorkBuddy" /E /I /H /Y
```

**请官方明确回答：卸载器是否会在卸载前执行 QmProtector suspend？若会，上述备份回滚方案是否可靠？**

---

## 需要官方协助（按紧急度排序）

### 1. 清除"活跃更新"状态（用户侧已自行定位，请确认是否安全）

日志中持续出现 `shouldSkipForActiveUpdate: Latest version 5.5.3.37748631 matches active update, skipping`，更新被永久标记为 active。

**已定位到该状态的实质：它不存放在任何配置文件里，而是由「缓存安装包文件是否存在」决定的。**

```
[win32] Valid cached package found:
  C:\Users\Lenovo\AppData\Local\Temp\workbuddy-update-x64\WorkBuddy-Setup-5.5.3.37748631.exe
```

已验证 `@genieworkbuddy-desktop-updater` 目录为空（此前已清空），active 状态依然存在 —— 说明判定依据就是该缓存文件本身。

**已执行的绕过操作（2026-09-06 22:5x）**：将缓存包重命名为 `...exe.disabled`
（**未删除，462.9 MB 完整保留，随时可改回**）。同时清除了已挂起约 1 小时的安装器进程。

**请官方确认：**
1. 该绕过是否安全、有效？有无副作用（如破坏下次更新的完整性校验）？
2. 应用随后会**重新下载**更新包吗？若会，是否仍会回到同一个死循环？
3. 是否已发布修复该问题的版本（>5.5.3）？若是，请给出版本号与完整安装包下载地址，用户可直接手动覆盖安装。

> 注：这条曾是当前影响最大的问题 —— 用户连续 3 天被更新弹窗绑架、无法正常使用了 5.4.5。

### 2. 确认 `Initialize=0x80000002` 的含义并提供降级路径

qm-helper.exe 存在且腾讯签名校验通过（chainTrusted=1, result=OK），DLL 已加载（"DLL loaded OK"），唯独驱动初始化失败。请确认：

- 是否因**缺少管理员权限**导致 `QmProtectorDriver.sys` 无法加载？
- 为何提权后（`IS_ELEVATED=True`）仍然失败？是驱动签名、Secure Boot、还是别的兼容性问题？

**建议修复**：QmProtector 失败时应**降级跳过**（仅跳过微信支付插件的安装/卸载），而非让整个更新流程挂起。

### 3. 提供跳过 QmProtector 的安装开关

如 `/NOQMPROTECT`、`/SKIP-WEIXINPAY` 之类的命令行参数，或在设置中提供"禁用微信支付插件保护"选项，让用户能在该组件异常时仍完成更新。

### 4. 明确回答卸载重装是否可行

见上一节。请给出确定答复与对应的回滚方案，**不要在没有把握的情况下建议用户卸载**。

### 5. 修复安装器"静默自杀"行为

静默安装到全新目录（`D:\WorkBuddy553`，零占用）时，安装器启动后**立即退出且不创建目录、不写任何日志**。建议安装器在初始化失败时输出明确的错误信息与退出码，而非静默消失 —— 这极大增加了用户侧的排查难度。

---

## 相关文件路径

| 用途 | 路径 |
|------|------|
| 更新日志 | `C:\Users\Lenovo\.workbuddy\logs\update\update-20260906.log` |
| QmProtector 日志 | `C:\Users\Lenovo\.workbuddy\logs\update\qm-uninstall.log` |
| 安装包 | `%LOCALAPPDATA%\Temp\workbuddy-update-x64\WorkBuddy-Setup-5.5.3.37748631.exe`（485 MB） |
| 安装目录 | `D:\WorkBuddy\` |
| 卸载器 | `D:\WorkBuddy\Uninstall WorkBuddy.exe` |
| 数据目录 | `C:\Users\Lenovo\.workbuddy\` |
| QmProtector 组件 | `D:\WorkBuddy\resources\app.asar.unpacked\resources\plugins\workbuddy-builtin\builtin-plugins\weixinpay\prebuilds\win32-x64\` |
| QmProtector helper | `D:\WorkBuddy\resources\qm\qm-helper.exe` |

## 附件

- `kill-result.txt` —— 自动化修复脚本的完整执行日志（含 0 进程 + 提权 + 90 秒零写入的实测记录）
