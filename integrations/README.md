# integrations

Connectors that let AI agents and automation tools operate
[YakYak](https://yakyak.ai/) — so a channel can be produced and published without
a human clicking through the UI.

Each subfolder wraps the [YakYak API](https://api.yakyak.ai/api/docs) for a
specific host environment.

| Integration | What it provides |
|-------------|------------------|
| [`claude/`](claude/) | Drive YakYak from Claude / Claude Code — tool definitions and an MCP server so an AI agent can create campaigns, generate episodes, and post. |
| [`codex/`](codex/) | Use YakYak from the OpenAI Codex CLI / agent environment. |
| [`n8n/`](n8n/) | n8n nodes and workflow templates to automate the YakYak pipeline visually. |

This section will be expanded over time as we integrate more deeply with existing
AI tools.

## Reference

- **API docs:** https://api.yakyak.ai/api/docs
- **OpenAPI spec:** https://api.yakyak.ai/api/docs-json

All integrations authenticate with a Bearer JWT from the **Users** API and build
on the same **Workflow** / **Scheduler** / **Social** endpoints documented in
[`../docs/`](../docs/).
