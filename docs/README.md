# docs

Conceptual documentation and guides for working with the [YakYak](https://yakyak.ai/) API.

Where the [SDKs](../sdk/) and [examples](../examples/) show *how* to call the API,
this folder explains *what the pieces mean* and how the production pipeline fits
together.

## Reference

- **Product:** https://yakyak.ai/
- **API docs (Swagger UI):** https://api.yakyak.ai/api/docs
- **OpenAPI spec (JSON):** https://api.yakyak.ai/api/docs-json

## The model in a nutshell

YakYak turns a premise into published, episodic video through a layered model:

- **Campaign** — your channel/show. Carries the look-and-feel: style, aspect
  ratio, animation, and quality settings. A campaign holds an ordered list of
  movies.
- **Movie** — a single episode. Owns a summary, a cast, a screenplay, a
  soundtrack, and the scenes that make it up.
- **Scene** — a unit of the screenplay: a title, a story/animation prompt, lead
  cast, dialogue, a generated background image, and the animated clip rendered
  from it.
- **Cast** — the characters: name, description, portrait image, assigned voice,
  and subtitle font/color.

See **[Workflows & use cases](workflows.md)** for a flow diagram of the pipeline
and the ways you re-enter it from a finished movie.

## The generation pipeline

A movie is produced by chaining `workflow/gen-*` steps, then rendered:

1. `gen-movie-summary` → synopsis
2. `gen-movie-cast` → character roster, then cast images, voices, and subtitle styling
3. `gen-movie-screenplay` → scenes with dialogue and prompts
4. `gen-movie-soundtrack` → music
5. `render-movie` → final video

Progress is observable (`get-movie-progress`, `get-scene-progress`), recoverable
(`resume`, `rerun-and-continue`, `regen-scene-asset`), and versioned
(`*-history` + `select-*` endpoints let you roll assets back).

## Scheduling & distribution

- **Scheduler** endpoints (`scheduler/set-frequency`, `set-next-trigger`,
  `enable-trigger`) automate rendering the next episode on an interval — the
  "auto-pilot" behavior.
- **Social** endpoints connect networks and auto-post each new episode
  (`social/connect-network`, `campaign-link`, `post-movie-batch`).

## Authentication

All endpoints (except public previews) require a Bearer JWT obtained via the
**Users** group (`create-by-email` → `confirm-email`, or `login-by-email`).
