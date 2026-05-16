# OpenClaw Plugin Marketplace

去中心化 Git-based 插件注册表。8 个 Community Skills + 4 个 MCP 服务器脚本。

## 使用

```bash
# 安装 marketplace 工具
pip install requests  # 或只用 stdlib
python3 marketplace.py sync     # 从 GitHub Pages 拉取注册表
python3 marketplace.py list     # 浏览所有插件
python3 marketplace.py install <name>  # 安装插件
```

## 注册表 URL

```
https://<your-username>.github.io/openclaw-plugins/registry.json
```

## 插件清单

| 插件 | 分类 | 版本 |
|------|------|------|
| mcp-bridge | integration | 1.0.0 |
| code-review | code-quality | 1.0.0 |
| test-generator | testing | 1.0.0 |
| doc-generator | documentation | 1.0.0 |
| session-tools | utilities | 1.0.0 |
| plugin-marketplace | system | 1.0.0 |
| ide-panel | ide | 1.0.0 |
| lsp | intelligence | 1.0.0 |
