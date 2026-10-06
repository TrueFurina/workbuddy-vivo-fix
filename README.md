# workbuddy-vivo-fix

WorkBuddy 安装卡死 & vivo 驱动修复的排障产物归档。

背景：WorkBuddy（Electron 应用）在本机安装/更新时反复卡死，根因涉及 WFP（Windows Filtering Platform）网络过滤驱动与服务死锁。本仓库归档另一 AI agent 排障过程中的诊断脚本、输出日志和修复记录，供同类问题参考。

## 目录结构

```
├── scripts/   诊断与修复脚本
├── logs/      诊断输出快照（驱动清单、事件日志、进程记录等）
└── docs/      修复记录与 bug 报告
```

## 关键文件

| 文件 | 说明 |
|------|------|
| `docs/WB安装卡死与防火墙死锁_永久修复记录.txt` | 核心修复记录：WFP 过滤驱动导致 Network Service 崩溃的死锁分析 |
| `docs/WorkBuddy-update-bug-report.md` | 更新流程 bug 报告 |
| `scripts/wfp_drv_check.py` | WFP 过滤驱动枚举检查 |
| `scripts/wfp_owner.py` | WFP 驱动归属判定 |
| `scripts/wb_drv_scan.py` | 驱动扫描 |
| `scripts/WorkBuddy_Force_Fix.bat` | 强制修复脚本 |
| `scripts/vivo_fix_install.bat` | vivo 驱动安装修复 |

## 免责声明

- 脚本为排障现场的一次性产物，以"现状"提供，使用前请阅读源码
- 涉及驱动枚举、进程强杀等操作，请在理解用途后于自己的环境执行
