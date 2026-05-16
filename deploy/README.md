# OpenClaw One-Click Deploy

跨平台一键部署脚本——10 分钟把普通 OpenClaw 升级为增强版。

## 平台支持

| 平台 | 脚本 | 命令 |
|------|------|------|
| **macOS** | `install.sh` | `bash install.sh` |
| **Ubuntu** | `install.sh` | `bash install.sh` |
| **Windows** | `install.ps1` | `powershell -ExecutionPolicy Bypass -File install.ps1` |

## 一键安装

```bash
# macOS / Ubuntu
curl -sL https://raw.githubusercontent.com/Douglas88/openclaw-plugins/main/deploy/install.sh | bash

# Windows (PowerShell 管理员)
powershell -Command "iwr https://raw.githubusercontent.com/Douglas88/openclaw-plugins/main/deploy/install.ps1 -OutFile install.ps1; .\install.ps1"
```

## 7 步自动化

| 步骤 | 内容 |
|------|------|
| 1. 环境检查 | Node.js 24 + Python 3.12 + Git |
| 2. 安装 OpenClaw | npm install -g openclaw@latest |
| 3. 安全配置 | exec=full + ask=off + 管道支持 |
| 4. Heartbeat | 三层监控清单 + 阈值警报 |
| 5. Skills | 7 个社区技能自动安装 |
| 6. MCP | 文件系统 + LSP + SQLite 服务器 |
| 7. 定时任务 | 每日安全审计 + 每周更新 + 每小时备份 |

## 选项

```
bash install.sh --dry-run       # 预览不执行
bash install.sh --skip-node      # 跳过 Node 安装
bash install.sh --skip-skills    # 跳过技能安装
bash install.sh --skip-mcp       # 跳过 MCP 配置
```

## 安装后

```bash
# 浏览插件
python3 ~/.openclaw/plugin-skills/plugin-marketplace/scripts/marketplace.py list

# 代码审查 — 直接对 OpenClaw 说 "review this file"
# 测试生成 — "generate tests for src/auth.py"
# 文档生成 — "generate API docs for app.py"

# 查看 MCP 服务器
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py list
```
