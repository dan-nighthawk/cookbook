# sdk

Client libraries for the [YakYak](https://yakyak.ai/) API.

The SDKs are generated from and kept in sync with the official OpenAPI
specification:

- **OpenAPI spec (source of truth):** https://api.yakyak.ai/api/docs-json
- **API docs (Swagger UI):** https://api.yakyak.ai/api/docs

Each client covers the full API surface — the **Users**, **Workflow**,
**Scheduler**, **Social**, and **Data** resource groups — handles Bearer-JWT auth,
and exposes typed models for the request/response schemas defined in the spec.

| SDK | Language |
|-----|----------|
| [`python/`](python/) | Python |
| [`javascript/`](javascript/) | JavaScript / TypeScript |

## Regenerating

Because the clients are derived from `docs-json`, they can be regenerated whenever
the API changes by pointing your OpenAPI generator at
`https://api.yakyak.ai/api/docs-json`. See each language folder for the exact
command.

## Publishing

Both SDKs are published as **`yakyak-sdk`** (PyPI and npm) by the manually-triggered
GitHub Actions workflow [`.github/workflows/publish-sdks.yml`](../.github/workflows/publish-sdks.yml).

Run it from the repo's **Actions** tab → *Publish SDKs* → *Run workflow*, supplying:

- **version** — the version to publish (must be new/unpublished)
- **target** — `both`, `pypi`, or `npm`
- **dry_run** — build and validate without publishing

The workflow generates fresh clients from `docs-json` at run time, builds them, and
uploads. It requires two repository secrets:

| Secret | Used for |
|--------|----------|
| `PYPI_API_TOKEN` | Publishing to PyPI (`twine`, token starting with `pypi-`) |
| `NPM_TOKEN` | Publishing to npm (automation/publish token) |
