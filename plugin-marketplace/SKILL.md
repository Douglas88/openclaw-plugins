---
name: plugin-marketplace
description: OpenClaw plugin marketplace - Git-based registry for discovering and installing plugins and skills. Use when: (1) discovering available plugins/skills, (2) installing plugins from git repos, (3) publishing plugins to share, (4) managing plugin dependencies. Uses git clone + file operations, no central server required.
version: "1.0.0"
---

# Plugin Marketplace

Git 仓库驱动的去中心化插件市场。无需中心服务器——用 GitHub/GitLab 仓库作为注册和分发渠道。

## 架构

```
plugin-registry.json (GitHub Gist / Repo)
  ├── plugin-a → https://github.com/user/plugin-a.git
  ├── plugin-b → https://github.com/user/plugin-b.git
  └── plugin-c → https://github.com/user/plugin-c.git

OpenClaw → read registry → git clone → activate
```

## 使用

### 发现插件

```bash
# 列出注册表中所有插件
python3 ~/.openclaw/plugin-skills/plugin-marketplace/scripts/marketplace.py list

# 搜索插件
python3 ~/.openclaw/plugin-skills/plugin-marketplace/scripts/marketplace.py search <keyword>

# 查看插件详情
python3 ~/.openclaw/plugin-skills/plugin-marketplace/scripts/marketplace.py info <plugin-name>
```

### 安装插件

```bash
python3 ~/.openclaw/plugin-skills/plugin-marketplace/scripts/marketplace.py install <plugin-name>
```

### 发布插件

```bash
# 注册插件到本地注册表
python3 ~/.openclaw/plugin-skills/plugin-marketplace/scripts/marketplace.py publish \
  --name <name> --repo <git-url> --category <category> --description "<desc>"
```

## 注册表格式

`~/.openclaw/plugin-registry.json`:

```json
{
  "version": 1,
  "registry": {
    "mcp-bridge": {
      "name": "mcp-bridge",
      "repo": "https://github.com/user/openclaw-mcp-bridge",
      "category": "integration",
      "description": "MCP protocol bridge for external tool integration",
      "version": "1.0.0",
      "author": "OpenClaw",
      "dependencies": []
    }
  }
}
```

## 安装流程

```
1. Read registry → find plugin entry
2. git clone <repo> → ~/.openclaw/plugin-skills/<name>/
3. Check dependencies
4. Verify SKILL.md / plugin.json exists
5. Enable in config
6. Done
```

Also update openclaw.json or skills config to include the new plugin path.
