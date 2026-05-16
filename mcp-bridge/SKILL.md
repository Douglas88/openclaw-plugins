---
name: mcp-bridge
description: OpenClaw MCP (Model Context Protocol) bridge for integrating external MCP servers as tools. Use when: (1) adding, listing, or removing MCP servers, (2) discovering tools from MCP servers, (3) calling tools on MCP servers (GitHub, database, file system, Slack, etc.), (4) accessing resources via MCP. Supports stdio and HTTP transports per MCP spec. All MCP interactions go through scripts/mcp_client.py and server management through scripts/mcp_manager.py.
version: "1.0.0"
---

# MCP Bridge - OpenClaw 模型上下文协议集成

OpenClaw 作为 MCP 客户端，通过此技能连接外部 MCP 服务器，发现和调用其提供的工具和资源。

## 架构

```
OpenClaw → mcp_client.py (JSON-RPC 2.0) → MCP Server → 外部服务
```

两种传输方式：
- **stdio**：启动本地进程，通过 stdin/stdout 通信（适合本地工具）
- **HTTP**：通过 HTTP POST 请求远程服务（适合云服务）

## 核心操作

### 1. 服务器管理

添加、查看、删除 MCP 服务器，使用 `scripts/mcp_manager.py`：

```bash
# 添加 stdio 服务器
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
  --name <name> --transport stdio --command <command> --args '<json_array>'

# 添加 HTTP 服务器
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
  --name <name> --transport http --url <url> --headers '<json_object>'

# 列出所有服务器
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py list

# 删除服务器
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py remove --name <name>
```

### 2. 工具发现

```bash
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action list_tools --server <name>
```

### 3. 工具调用

```bash
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action call_tool \
  --server <name> --tool <tool_name> --args '<json_args>'
```

### 4. 资源访问

```bash
# 列出资源
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action list_resources --server <name>

# 读取资源
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action read_resource --server <name> --uri <uri>
```

## 使用工作流

### 场景1：使用 GitHub MCP 搜索仓库

```bash
# 第一步：添加服务器（只需一次）
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
  --name github --transport http \
  --url https://api.githubcopilot.com/mcp/ \
  --headers '{"Authorization":"Bearer $GITHUB_TOKEN"}'

# 第二步：查看可用工具
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action list_tools --server github

# 第三步：调用工具
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action call_tool \
  --server github --tool search_repos --args '{"query":"claude code agent","limit":5}'
```

### 场景2：使用数据库 MCP 查询

```bash
# 添加 PostgreSQL MCP
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
  --name db --transport stdio --command npx \
  --args '["-y","@bytebase/dbhub"]' \
  --env '{"DB_URL":"postgresql://user:pass@localhost:5432/mydb"}'

# 查询
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action call_tool \
  --server db --tool query --args '{"sql":"SELECT * FROM users LIMIT 10"}'
```

### 场景3：使用 Playwright MCP 进行浏览器测试

```bash
# 添加 Playwright
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py add \
  --name playwright --transport stdio --command npx \
  --args '["-y","@playwright/mcp@latest"]'

# 截取网页
python3 ~/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_client.py --action call_tool \
  --server playwright --tool browser_snapshot --args '{"url":"https://example.com"}'
```

## 重要约束

1. **不要硬编码凭证**：使用环境变量或让用户提供 tokens
2. **stdio 需要已安装命令**：如 `npx`、`python` 等必须在 PATH 中
3. **HTTP 服务器需要网络可达**：远程 URL 必须可访问
4. **工具调用有超时**：默认 30 秒，可在 mcp_client.py 中修改
5. **配置文件位置**：`~/.openclaw/mcp_servers.json`
6. **错误处理**：所有脚本返回 JSON，检查 `error` 字段

## 参考

- MCP 协议详情：见 `references/mcp_protocol.md`
- 热门 MCP 服务器：https://github.com/modelcontextprotocol/servers
