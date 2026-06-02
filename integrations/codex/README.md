# integrations/codex

Operate [YakYak](https://yakyak.ai/) from the **OpenAI Codex** CLI / agent
environment.

This integration gives a Codex-driven agent the configuration and helpers it needs
to call the [YakYak API](https://api.yakyak.ai/api/docs) — authenticating, then
creating campaigns, generating episodes, rendering, and posting to social
networks.

## What's here

- **Agent configuration** wiring the YakYak API into a Codex workflow.
- **Auth helper** for obtaining a Bearer JWT from the **Users** API.
- **Recipes** that walk the agent through the generation pipeline
  (`gen-movie-*` → `render-movie` → `social/post-movie-batch`).

## Reference

- **API docs:** https://api.yakyak.ai/api/docs
- **OpenAPI spec:** https://api.yakyak.ai/api/docs-json

Built on the same [SDK](../../sdk/) clients used elsewhere in this cookbook.
