# integrations/claude

Operate [YakYak](https://yakyak.ai/) from **Claude** — including Claude Code and
the Claude Agent SDK.

This integration exposes the [YakYak API](https://api.yakyak.ai/api/docs) as tools
an AI agent can call, so Claude can run the whole media pipeline conversationally:
create a campaign, generate a summary, cast, and screenplay, render the movie, and
post it to connected social networks.

## What's here

- **MCP server / tool definitions** mapping YakYak **Workflow**, **Scheduler**,
  **Social**, and **Data** endpoints to agent-callable tools.
- **Auth helper** for exchanging credentials for a Bearer JWT (`users/login-by-email`).
- **Prompts / recipes** showing Claude how to orchestrate the generation steps
  end-to-end.

## Reference

- **API docs:** https://api.yakyak.ai/api/docs
- **OpenAPI spec:** https://api.yakyak.ai/api/docs-json

The tool surface is built on the same [SDK](../../sdk/) clients used elsewhere in
this cookbook.
