# OpenClaw Plugin Marketplace

去中心化 Git-based 插件注册表。当前注册表包含 18 个 Community Skills、MCP scripts 和 agent workflows。

## 使用

```bash
python3 plugin-marketplace/scripts/marketplace.py sync
python3 plugin-marketplace/scripts/marketplace.py list
python3 plugin-marketplace/scripts/marketplace.py install <name>
```

## 注册表 URL

```
https://douglas88.github.io/openclaw-plugins/registry.json
```

## npm OpenClaw 插件

本仓库的 marketplace 工具适合通过 Git 克隆安装的 skills/plugins。原生 npm OpenClaw 插件应使用 OpenClaw CLI 安装，不要复制到 `plugin-skills/`。

示例：

```bash
openclaw plugins install @xquik/tweetclaw
```

[TweetClaw](https://github.com/Xquik-dev/tweetclaw) 是用于 X/Twitter automation 的 OpenClaw 插件，支持 scrape tweets、search tweets、search tweet replies、post tweets、post tweet replies、follower export、user lookup、media upload、media download、direct messages、monitor tweets、webhooks 和 giveaway draws。将认证材料放在本地 OpenClaw 配置中，并在公开发布或回复前进行人工确认。

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
| desktop-automation | desktop | 1.0.0 |
| codex-mode | coding | 1.0.0 |
| claude-mode | coding | 1.0.0 |
| reasoning-engine | intelligence | 1.0.0 |
| multimodal-bridge | multimodal | 1.0.0 |
| manus-agent | agent | 1.0.0 |
| deep-research | research | 1.0.0 |
| data-pipeline | data | 1.0.0 |
| security-scanner | security | 1.0.0 |
| bounty-hunter | security | 1.0.0 |
