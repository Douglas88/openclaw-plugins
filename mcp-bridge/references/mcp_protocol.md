# OpenClaw MCP Bridge

OpenClaw 实现的 Model Context Protocol (MCP) 客户端。  
使用 JSON-RPC 2.0 协议，支持 stdio 和 HTTP 两种传输方式，让 OpenClaw 可以调用外部 MCP 服务器提供的工具和资源。

## 快速开始

### 1. 添加 MCP 服务器

```bash
# stdio 传输（本地进程）
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
  --name github \
  --transport stdio \
  --command npx \
  --args '["-y","@anthropic/mcp-server-github"]'

# HTTP 传输（远程服务）
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
  --name slack \
  --transport http \
  --url https://mcp.slack.com/mcp \
  --headers '{"Authorization":"Bearer x-your-token"}'

# 带环境变量
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
  --name db \
  --transport stdio \
  --command npx \
  --args '["-y","@bytebase/dbhub"]' \
  --env '{"DB_URL":"postgresql://localhost/mydb"}'
```

### 2. 查看服务器列表

```bash
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py list
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action list_servers --server any
```

### 3. 列出可用工具

```bash
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action list_tools --server github
```

### 4. 调用工具

```bash
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action call_tool \
  --server github \
  --tool search_repos \
  --args '{"query":"openclaw","limit":10}'
```

### 5. 管理服务器

```bash
# 查看服务器详情
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py get --name github

# 删除服务器
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py remove --name github
```

## 支持的操作

| 操作 | MCP 方法 | 对应命令 |
|------|---------|---------|
| 初始化连接 | `initialize` | `--action ping` |
| 列出工具 | `tools/list` | `--action list_tools` |
| 调用工具 | `tools/call` | `--action call_tool --tool <name>` |
| 列出资源 | `resources/list` | `--action list_resources` |
| 读取资源 | `resources/read` | `--action read_resource --uri <uri>` |

## 热门外 MCP 服务器添加示例

### 开发工具
```bash
# GitHub
mcp_manager.py add --name github --transport http --url https://api.githubcopilot.com/mcp/ --headers '{"Authorization":"Bearer $GITHUB_TOKEN"}'

# GitLab
mcp_manager.py add --name gitlab --transport stdio --command npx --args '["-y","@gitlab/mcp-server"]'

# Playwright (浏览器测试)
mcp_manager.py add --name playwright --transport stdio --command npx --args '["-y","@playwright/mcp@latest"]'
```

### 数据库
```bash
# PostgreSQL
mcp_manager.py add --name postgres --transport stdio --command npx --args '["-y","@bytebase/dbhub"]' --env '{"DB_URL":"postgresql://user:pass@localhost:5432/db"}'

# SQLite
mcp_manager.py add --name sqlite --transport stdio --command npx --args '["-y","@anthropic/mcp-server-sqlite"]'
```

### 监控
```bash
# Sentry
mcp_manager.py add --name sentry --transport http --url https://mcp.sentry.dev/mcp --headers '{"Authorization":"Bearer $SENTRY_TOKEN"}'
```

### 文件系统
```bash
# 本地文件系统
mcp_manager.py add --name filesystem --transport stdio --command npx --args '["-y","@anthropic/mcp-server-filesystem","/path/to/allowed/dir"]'
```

## 工作原理

```
OpenClaw Agent
    │
    ▼
read/exec: mcp_client.py --action call_tool --server X --tool Y
    │
    ▼
mcp_client.py → JSON-RPC 2.0 请求
    │
    ├── stdio: subprocess + stdin/stdout
    └── HTTP: urllib POST
    │
    ▼
MCP Server → 处理请求 → 返回结果
    │
    ▼
JSON-RPC 2.0 响应 → 输出到 stdout → Agent 读到结果
```

## 配置文件

服务器配置存储在 `~/.openclaw/mcp_servers.json`：

```json
{
  "version": 1,
  "servers": {
    "github": {
      "transport": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {"Authorization": "Bearer xxx"}
    },
    "playwright": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"],
      "env": {},
      "description": "Browser automation via Playwright"
    }
  }
}
```

## 扩展指南

### 添加更多 MCP 方法

编辑 `mcp_client.py`，在 `MCPStdioClient` 和 `MCPHttpClient` 类中添加新方法：

```python
def list_prompts(self) -> dict:
    return self._send_request("prompts/list")

def get_prompt(self, name: str) -> dict:
    return self._send_request("prompts/get", {"name": name})
```

### 添加新传输方式

继承 `MCPStdioClient` 的模式，实现新的传输类。
