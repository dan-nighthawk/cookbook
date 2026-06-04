# Course: build your first AI movie with the YakYak API

A hands-on, copy-paste course that takes you from zero to a **rendered, shareable
movie** — then layers in scenes, cast, soundtrack, your own media, and publishing.

Every step is shown in **three languages**: `curl`/bash, JavaScript/TypeScript, and
Python. Pick the one you like; they all hit the same [YakYak API](https://api.yakyak.ai/api/docs).

> This is **step 1** of a longer journey. Once you can drive the API by hand, the
> [What's next](#whats-next) section points to driving it from coding agents, on a
> schedule, and as one-click scripts.

## The arc

| # | Lesson | You'll learn |
|---|--------|--------------|
| 1 | [Sign up & get your token](01-signup.md) | Create an account, confirm your email, get a Bearer token |
| 2 | [Hello, world — your first movie](02-hello-world.md) ⭐ | Campaign → movie → one Ken Burns scene → **render → shareable link** |
| 3 | Pick your look & animation | Styles, aspect ratio, Ken Burns vs Kling |
| 4 | Add a new scene | Grow the screenplay |
| 5 | Cast: characters, roles & images | AI cast, custom characters, portraits |
| 6 | Soundtrack | Reuse, generate, or skip music |
| 7 | Bring your own images | Upload art for a scene |
| 8 | Bring your own clips | Drop in prerendered video |
| 9 | Publish to social | Connect a network and post |
| 10 | Advanced | Basic vs Pro mode, progress & recovery |

Lessons 3–10 land after you've validated the flow in 1–2.

## Setup

### 1. Base URL

```
https://api.yakyak.ai          # production
https://api.beta.yakyak.ai     # beta
```

> Endpoints are served at the **root** (e.g. `POST https://api.yakyak.ai/workflow/create-campaign`).
> Only the interactive docs live under `/api` ([Swagger UI](https://api.yakyak.ai/api/docs),
> [OpenAPI JSON](https://api.yakyak.ai/api/docs-json)).

### 2. Environment variables

The lessons read everything from the environment — never hard-code secrets.

```bash
export YAKYAK_API_BASE="https://api.yakyak.ai"
export YAKYAK_EMAIL="you@example.com"
export YAKYAK_PASSWORD="a-strong-password"
# Filled in during Lesson 1:
export YAKYAK_TOKEN=""     # Bearer JWT
export YAKYAK_USER_ID=""   # your user id (most write calls need it)
```

### 3. Install an SDK (optional, for JS/Python)

There's an official SDK on both registries — handy for the simple reads:

```bash
npm install yakyak-sdk      # JavaScript / TypeScript
pip install yakyak-sdk      # Python  (module: yakyak_sdk)
```

```js
import { YakYakClient } from "yakyak-sdk";
const yak = new YakYakClient({ baseUrl: process.env.YAKYAK_API_BASE, token: process.env.YAKYAK_TOKEN });
const styles = await yak.data.getStyles();   // { success, count, styles: [...] }
```

The course's runnable code uses plain HTTP (`curl` / `fetch` / `requests`) so every
call is transparent and copy-pasteable, but anything you see maps 1:1 onto the SDK
(`POST /workflow/create-campaign` → `yak.workflow.createCampaign({...})`).

## Conventions

**Two tiny helpers** appear in every lesson — define them once per language.

```bash
# bash: api <METHOD> <path> [json-body]
api() { local m=$1 p=$2 body=${3:-}; curl -s -X "$m" "$YAKYAK_API_BASE$p" \
  -H "Authorization: Bearer $YAKYAK_TOKEN" -H "Content-Type: application/json" \
  ${body:+-d "$body"}; }
```

```js
// js: api(method, path, body?) -> parsed JSON
const api = async (method, path, body) => {
  const res = await fetch(process.env.YAKYAK_API_BASE + path, {
    method,
    headers: { Authorization: `Bearer ${process.env.YAKYAK_TOKEN}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${path} -> ${res.status} ${await res.text()}`);
  return res.status === 204 ? null : res.json();
};
```

```python
# python:  api("POST", "/path", {...}) -> parsed JSON   (pip install requests)
import os, requests
def api(method, path, body=None):
    r = requests.request(method, os.environ["YAKYAK_API_BASE"] + path,
        headers={"Authorization": f"Bearer {os.environ.get('YAKYAK_TOKEN','')}"}, json=body)
    r.raise_for_status()
    return r.json() if r.content else None
```

**Polling.** Generation is asynchronous. You start a step, then poll a progress
endpoint until it's `completed`. Each lesson shows the exact poll; the pattern is
always "kick off → poll `get-*-progress` → continue".

**Cost legend.** Some steps spend render credits and take time:

| | Meaning |
|---|---------|
| ✅ | Free/fast — runs in the default flow (auth, edits, **Ken Burns**, concat, uploads) |
| 💸 | Paid/slow — shown but **opt-in** (Kling video, AI cast images, AI soundtrack) |

This course's default path stays on the ✅ side.

## What's next

1. **Coding agents** — let an AI agent operate YakYak for you (see [`../integrations/`](../integrations/)).
2. **On a schedule** — a reusable script that ships an episode on an interval (`scheduler/*`).
3. **One-click runners** — package your script so anyone can run it.

---

Reference: [API docs](https://api.yakyak.ai/api/docs) ·
[concepts](../docs/) · [workflow diagram](../docs/workflows.md) · [SDKs](../sdk/)
