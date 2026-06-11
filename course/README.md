# Course: build your first AI movie with the YakYak API

A hands-on course of **complete, runnable scripts** — no copy-paste. Each lesson
ships the same program in three languages:

- **bash** — plain `curl` (no dependencies)
- **JavaScript** — the [`yakyak-sdk`](../sdk/javascript/) client
- **Python** — the [`yakyak-sdk`](../sdk/python/) client

Run one, read the others. You go from zero to a **rendered, shareable movie**, then
layer in scenes, cast, soundtrack, your own media, and publishing.

> **Step 1** of a longer journey — see [What's next](#whats-next) for driving the
> API from coding agents, on a schedule, and as one-click scripts.

## The arc

| # | Lesson | You'll learn |
|---|--------|--------------|
| 1 | [Sign up & get your token](01-signup/) | Create an account, confirm email, save a token to `.env` |
| 2 | [Hello, world](02-hello-world/) ⭐ | **Fork Fruit Island** and **render → shareable link** |
| 3 | [Create your own campaign](03-new-campaign/) | From a prompt: custom cast with uploaded portraits, a Ken Burns scene, render |
| 4 | [Edit your movie](04-edit-movie/) | AI screenplay, then delete a scene, add a Narrator (cinematic voice) & an AI Guru |
| 5 | [Bring your own image + AI animation](05-byo-image/) | Upload a pre-rendered still, animate it with Kling, voice it with your Narrator |
| 6 | [Add a pre-rendered intro clip](06-intro-clip/) | Upload your own opening video and prepend it as scene 1 |
| 7 | [Soundtrack](07-soundtrack/) | Upload your own music or compose an AI score (and reuse or skip) |
| 8 | [Publish to social](08-social-post/) | Connect a network and post your movie ([watch the result](https://www.youtube.com/watch?v=TBq5_CwhxdI)) |

## Setup

### 1. Configure `.env`

From this `course/` folder:

```bash
cp .env.example .env
# edit .env: set YAKYAK_EMAIL and YAKYAK_PASSWORD
```

`.env` (the scripts read it and write your token back into it):

```
YAKYAK_API_BASE=https://api.yakyak.ai   # YakYak API base
YAKYAK_EMAIL=you@example.com
YAKYAK_PASSWORD=…
YAKYAK_TOKEN=                                 # filled in by Lesson 1
YAKYAK_USER_ID=                               # filled in by Lesson 1
YAKYAK_TUTORIAL_MOVIE_ID=                     # the episode Lesson 2 forks
```

> **Base URL is overridable everywhere** — bash uses `$YAKYAK_API_BASE`, and the
> SDK clients take it as a constructor option (`new YakYakClient({ baseUrl })` /
> `Configuration(host=…)`), so you can point the same scripts at any YakYak API host.

### 2. Prerequisite: SDK ≥ 0.0.7

The JS/Python lessons call the SDK's workflow methods (e.g.
`client.workflow.createCampaign({ … })`). Those require **`yakyak-sdk` 0.0.7+**,
which adds request bodies the earlier builds were missing (see
[`sdk/patch-spec.py`](../sdk/patch-spec.py)). Install per language:

```bash
npm install                      # JS — reads course/package.json
pip install -r requirements.txt  # Python
```

The **bash** lessons use only `curl` + `python3` (for JSON) and need no SDK.

## Conventions

- **Run from the `course/` folder.** Scripts resolve `.env` relative to it.
- **Cost legend.** ✅ free/fast (auth, edits, **Ken Burns**, concat, uploads);
  💸 paid/slow, shown but opt-in (Kling video, AI cast images, AI soundtrack).
- **Polling.** Generation is async — scripts kick off a step then poll a
  `get-*-progress` endpoint until it's `completed`.

## What's next

1. **Coding agents** — let an AI agent operate YakYak (see [`../integrations/`](../integrations/)).
2. **On a schedule** — a reusable script that ships an episode on an interval (`scheduler/*`).
3. **One-click runners** — package your script so anyone can run it.

---

Reference: [API docs](https://api.yakyak.ai/api/docs) ·
[concepts](../docs/) · [workflow diagram](../docs/workflows.md) ·
[debugging](../docs/debugging.md) · [SDKs](../sdk/)

> **Stuck?** If a render never finishes or a scene comes back blank, see
> [Debugging](../docs/debugging.md) — it covers reading AI-generation failures on
> the `/profile` page and diagnosing failing GitHub Actions.
