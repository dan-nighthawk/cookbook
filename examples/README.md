# examples

End-to-end, runnable recipes that drive the [YakYak](https://yakyak.ai/) API.

Each example is a self-contained walkthrough of a real task — authenticate,
create a campaign, generate an episode, render it, and post it to a social
network — using one of the [SDKs](../sdk/) or plain HTTP calls.

## Reference

- **API docs:** https://api.yakyak.ai/api/docs
- **OpenAPI spec:** https://api.yakyak.ai/api/docs-json

## Suggested recipes

A typical "hello, channel" flow stitches together the **Workflow**, **Scheduler**,
and **Social** endpoints:

1. **Authenticate** — `users/create-by-email` → `users/confirm-email`, or
   `users/login-by-email`, to obtain a Bearer JWT.
2. **Pick a look** — fetch `data/style`, `data/voice`, and `data/font`.
3. **Create a campaign** — `workflow/create-campaign` with your chosen style and
   settings.
4. **Generate an episode** — `start-campaign`, then chain `gen-movie-summary` →
   `gen-movie-cast` → `gen-movie-screenplay` → `gen-movie-soundtrack`.
5. **Render** — `workflow/render-movie`, polling `get-movie-progress`.
6. **Connect & post** — `social/connect-network`, `social/campaign-link`, then
   `social/post-movie-batch`.
7. **Automate** — `scheduler/set-frequency` + `enable-trigger` to ship the next
   episode on a schedule.

## Conventions

- Examples read credentials from environment variables (e.g. `YAKYAK_API_TOKEN`);
  never hard-code tokens.
- Each example notes which SDK it uses and how to run it.
