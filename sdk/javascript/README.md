# sdk/javascript

JavaScript / TypeScript client for the [YakYak](https://yakyak.ai/) API, generated
from the official OpenAPI specification.

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

It handles Bearer-JWT authentication and ships TypeScript types for the
request/response schemas (e.g. `CampaignResponseDto`, `CastMemberDto`,
`RenderMovieRequestDto`).

## Install & use

```bash
npm install yakyak-sdk
```

```ts
import { YakYakClient } from "yakyak-sdk";

const client = new YakYakClient({
  baseUrl: "https://api.yakyak.ai",
  token: process.env.YAKYAK_API_TOKEN,
});

const styles = await client.data.getStyles();
const campaign = await client.workflow.createCampaign({ /* ... */ });
```

> Published on npm as **`yakyak-sdk`**; export names follow the generator
> config — see the source in this folder.

## Regenerating

Regenerate against the live spec when the API changes:

```bash
npx @openapitools/openapi-generator-cli generate \
  -i https://api.yakyak.ai/api/docs-json \
  -g typescript-fetch \
  -o .
```
