# sdk/python

Python client for the [YakYak](https://yakyak.ai/) API, generated from the official
OpenAPI specification.

- **OpenAPI spec (source of truth):** https://api.yakyak.ai/api/docs-json
- **API docs:** https://api.yakyak.ai/api/docs

## Scope

The client covers the full API surface defined in the spec:

- **Users** — account creation, email confirmation, login, profile, tokens.
- **Workflow** — campaigns, movies, scenes, the `gen-movie-*` generation steps,
  rendering, media/assets, and progress.
- **Scheduler** — automated render triggers and frequency.
- **Social** — network connections and posting.
- **Data** — styles, voices, fonts.

It handles Bearer-JWT authentication and provides typed models for the
request/response schemas (e.g. `CampaignResponseDto`, `CastMemberDto`,
`RenderMovieRequestDto`).

## Install & use

```bash
pip install yakyak-sdk
```

```python
from yakyak_sdk import Client

client = Client(base_url="https://api.yakyak.ai", token="<JWT>")
styles = client.data.list_styles()
campaign = client.workflow.create_campaign(...)
```

> Distributed on PyPI as **`yakyak-sdk`**; the importable module is `yakyak_sdk`.
> Names follow the generator config; see the source in this folder.

## Regenerating

Regenerate against the live spec when the API changes:

```bash
openapi-python-client generate --url https://api.yakyak.ai/api/docs-json
```
