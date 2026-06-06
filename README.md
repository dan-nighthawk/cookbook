# YakYak Cookbook

How to use **[YakYak](https://yakyak.ai/)** as a Human or AI Agent.

YakYak is an autonomous AI media agency. It writes,
casts, voices, and ships episodic video for your channel on auto-pilot. You pick a
style and a premise; YakYak generates the plot, cast, screenplay, scenes,
soundtrack, and renders, then publishes each episode to your connected social
networks on a schedule.

For greater control you can also connect your own AI agents to the APIs to gain
fine grained control of every aspect of the creative pipeline.

This cookbook is a collection of recipes, client libraries, and integrations for
driving that pipeline programmatically through the YakYak API.

## Reference

- **Product:** https://yakyak.ai/
- **API docs (Swagger UI):** https://api.yakyak.ai/api/docs
- **OpenAPI spec (JSON):** https://api.yakyak.ai/api/docs-json

The API is organized into five resource groups: **Users** (auth & accounts),
**Workflow** (campaigns, movies, scenes, generation, rendering), **Scheduler**
(automated render triggers), **Social** (network connections & posting), and
**Data** (styles, voices, fonts). All endpoints use Bearer-JWT auth.

## Repository layout

| Folder | What's inside |
|--------|---------------|
| [`course/`](course/) | Hands-on, copy-paste course (curl · JS · Python) — from signup to a rendered, shareable movie. **Start here.** |
| [`docs/`](docs/) | Concepts, glossary, and guides for the YakYak API and workflow model. |
| [`sdk/`](sdk/) | Client libraries generated from the OpenAPI spec — [Python](sdk/python/) and [JavaScript/TypeScript](sdk/javascript/). |
| [`examples/`](examples/) | End-to-end, runnable recipes that drive the API (create campaign → generate → render → post). |
| [`integrations/`](integrations/) | Connectors that let AI agents and automation tools operate YakYak — [Claude](integrations/claude/), [Codex](integrations/codex/), [n8n](integrations/n8n/). |
| [`community/`](community/) | Community-contributed campaigns and channel showcases. |

## License

See [LICENSE](LICENSE).
