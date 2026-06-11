# `upload_to_yakyak` — Usage

End-to-end driver that pushes the newest Breaking Bricks News story into a
YakYak campaign, waits for scene generation, attaches the BBN soundtrack,
renders the final episode, and (optionally) posts it to every social network
linked to the campaign.

> **⚠️ Moved + generalized (2026-06).** The engine now lives at
> **`marketing/showrunner/`** (`upload_to_yakyak.{sh,py,js}`) and is
> **show-agnostic**: it takes `--show <showDir>` and reads per-show settings from
> `<showDir>/show.env`. BBN is now `marketing/BreakingBricksNews/` (config +
> `prompt.md`, no scripts). **The canonical reference is
> [`../../showrunner/README.md`](../../showrunner/README.md)** — start there.
> Story sourcing moved from `prepare_latest.sh` to the generic
> `showrunner/prepare.sh <showDir>` + the show's `prompt.md`. Auth is a PAT
> (`YAKYAK_PAT`, legacy `YAKYAK_BB_PAT` still honored), not email/password.
> Invocations below that read `./upload_to_yakyak.sh [campaignId]` are historical;
> the equivalent today is `showrunner/upload_to_yakyak.sh --show marketing/BreakingBricksNews`.

---

## Quick reference

```bash
./upload_to_yakyak.sh [campaignId] [storyFile] [flags]
```

| Argument / flag             | Default                                                                            | Meaning                                                                                       |
| --------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `campaignId` *(positional)* | `62c9e486-2a80-49dd-afeb-5c5dba416cb9` (BBN production)                            | Which campaign to write into.                                                                 |
| `storyFile` *(positional)*  | newest file matching the show's `STORY_GLOB` in `<showDir>/stories/`               | Markdown story produced by `showrunner/prepare.sh`.                                           |
| `--post`                    | off                                                                                | After render finishes, post to every social network linked to the campaign.                   |
| `--post-only`               | off                                                                                | Skip upload + render entirely; only post an already-rendered episode. Implies `--post`.       |
| `--movie <movieId>`         | —                                                                                  | Pin the run to a specific movie ID instead of the auto picker. Works in both modes.           |
| `--volume <N>`              | `45`                                                                               | Soundtrack volume percentage (0–100).                                                         |
| `--soundtrack <audioPath>`  | the BBN intro track captured from the web app                                      | Override the default soundtrack. Falls back to `items[0]` of `available-soundtracks` if the supplied path isn't in the pool for the chosen movie. |
| `--skip-finalize`           | off                                                                                | Stop after kicking off screenplay regen — no scene wait, no soundtrack, no render. Useful if you want to finalise later by hand. Mutually exclusive with `--post-only`. |
| `-h`, `--help`              | —                                                                                  | Print embedded help.                                                                          |

Environment (loaded from `e2e/.env.bb`):

| Variable                 | Default                       | Notes                                                                  |
| ------------------------ | ----------------------------- | ---------------------------------------------------------------------- |
| `YAKYAK_BB_EMAIL`        | `bb@yakyak.ai`                | Account that owns the campaign.                                        |
| `YAKYAK_BB_PASSWORD`     | *(required)*                  | If empty the script aborts.                                            |
| `YAKYAK_API_URL`         | `https://api.yakyak.ai`  | Override to point at a different YakYak API host.                      |

---

## Modes

### Default mode — upload, render, exit

```bash
./upload_to_yakyak.sh
```

What happens, in order:

1. **Token-balance gate.** `GET /users/<userId>` (userId comes from the login
   response). If `tokenBalance < 2000` the script warns and prompts `y/N`
   on a TTY, or aborts non-interactively (cron-safe).
2. **Login.** `POST /users/login-by-email` → JWT + `userId`.
3. **Pick episode.** Lowest-`(season, episode)` movie in the campaign with
   `status != "completed"` AND `renderedMovieUrl == ""`. If none exist,
   `POST /workflow/create-new-season` and poll ~3 min for new episodes.
4. **Set metadata.** `POST /workflow/set-movie-metadata` with the flat-bullet
   description converted from the story markdown.
5. **Set social caption + title.** `POST /workflow/update-movie-social-description`
   (caption is the `## Headlines we drew from` section; title is generated by
   `claude -p`, max 50 chars).
6. **Kick generation.** `POST /workflow/gen-movie-screenplay`.
7. **Wait for scenes.** Poll `GET /workflow/get-movie/<movieId>` every 15s for
   up to ~30 min, until every `scene[].sceneBurnSubtitle.status == "completed"`.
   Aborts immediately if any scene goes `"failed"`.
8. **Attach soundtrack.** `GET /workflow/available-soundtracks/<movieId>`,
   match the preferred `audioPath` (default = BBN intro) or fall back to
   `items[0]`, then `POST /workflow/set-soundtrack-audio`.
9. **Set volume.** `POST /workflow/set-soundtrack` with
   `{ movieId, volumePercentage }`.
10. **Render.** `POST /workflow/export-render` `{ movieId, force: false }`.
11. **Wait for render.** Poll `GET /workflow/render-history/<movieId>` every 5s
    for up to ~15 min, until `items[0].finishedAt` appears. Prints the resulting
    `soundtrackedMovieUrl`.
12. *(no posting)* Exits.

### `--post` — upload, render, **and** post

```bash
./upload_to_yakyak.sh --post
```

Identical to default mode, plus a final social-posting block:

13. `GET /social/campaign-links/<campaignId>` → list of connected networks.
14. For each linked network: `POST /social/post-movie/<movieId>/<connectedNetworkId>`.
    Per-network 4xx responses are logged and counted but **do not abort the
    loop** — useful because PFM sometimes 429s on rapid bursts and the backend's
    own batched retry handles most of them.

Because the render-wait in step 11 is blocking, by the time the social posts
fire the CDN URL is live and the linked networks can pick it up.

### `--post-only` — post an already-rendered episode

```bash
# Most common form: just post the latest rendered episode in the campaign
./upload_to_yakyak.sh --post-only

# Or pin it to a specific movie ID (e.g. one you grabbed from a prior run)
./upload_to_yakyak.sh --post-only --movie 61fd9c11-d231-486a-971d-d32de0163e8a
```

`--post-only` implies `--post`. The script:

- **Skips** the story file (you don't even need one), the token-balance gate
  (posting doesn't burn tokens), set-metadata, social-caption write, screenplay
  regen, scene wait, soundtrack assignment, volume set, render trigger, and
  render wait.
- **Selects** the episode as follows:
  - If `--movie <id>` is passed: that exact movie (verified to exist in the
    campaign first).
  - Otherwise: the **highest-`(season, episode)` movie with a non-empty
    `renderedMovieUrl`** — i.e. the most recently rendered episode, which is
    what you almost always want right after a default-mode run.
- **Runs** only the `campaign-links` → `post-movie` loop.

Combining `--post-only` with `--skip-finalize` is rejected as contradictory.

---

## Recommended workflows

### Two-step: render now, post later

Use this when you want to eyeball the rendered MP4 in
[https://yakyak.ai/export](https://yakyak.ai/export?movieId=…) before
broadcasting it everywhere.

```bash
# 1. Generate, render, wait. No posting.
./upload_to_yakyak.sh

# 2. Inspect the printed Preview URL. When happy:
./upload_to_yakyak.sh --post-only
```

### One-shot: render and post in a single run

For automated cron runs where you're confident in the pipeline.

```bash
./upload_to_yakyak.sh --post
```

### Re-post an old episode

```bash
./upload_to_yakyak.sh --post-only --movie <movieId>
```

### Generate now, finalise later by hand in the UI

```bash
./upload_to_yakyak.sh --skip-finalize
```

This stops right after `gen-movie-screenplay`, so you can fiddle with the
storyboard / scenes / soundtrack manually before hitting **Render** in the
export page.

### Different soundtrack or volume

```bash
./upload_to_yakyak.sh \
  --volume 35 \
  --soundtrack "prd/ugc/.../audio/<other-track-uuid>.mp3"
```

The `--soundtrack` value must be an `audioPath` (not the CDN URL) and must
appear in `/workflow/available-soundtracks/<movieId>` for the chosen movie. If
it doesn't, the script silently falls back to `items[0]` and prints a notice —
useful so you can never accidentally end up with no soundtrack at all.

---

## API surface used

| Step                       | Method | Endpoint                                                    |
| -------------------------- | ------ | ----------------------------------------------------------- |
| Login                      | POST   | `/users/login-by-email`                                     |
| Token balance              | GET    | `/users/<userId>`                                           |
| Pick episode               | GET    | `/workflow/get-campaign/<campaignId>`                       |
| New season (fallback)      | POST   | `/workflow/create-new-season`                               |
| Set description            | POST   | `/workflow/set-movie-metadata`                              |
| Set caption + title        | POST   | `/workflow/update-movie-social-description`                 |
| Kick generation            | POST   | `/workflow/gen-movie-screenplay`                            |
| Poll scene readiness       | GET    | `/workflow/get-movie/<movieId>`                             |
| List soundtracks           | GET    | `/workflow/available-soundtracks/<movieId>`                 |
| Attach soundtrack          | POST   | `/workflow/set-soundtrack-audio`                            |
| Set volume                 | POST   | `/workflow/set-soundtrack`                                  |
| Trigger render             | POST   | `/workflow/export-render`                                   |
| Poll render finished       | GET    | `/workflow/render-history/<movieId>`                        |
| List campaign networks     | GET    | `/social/campaign-links/<campaignId>`                       |
| Post to one network        | POST   | `/social/post-movie/<movieId>/<connectedNetworkId>`         |

All authenticated calls send `Authorization: Bearer <jwt>` (JWT from the login
step).

---

## Polling cadence

| Loop                  | Interval | Max iterations | Total budget |
| --------------------- | -------- | -------------- | ------------ |
| New-season episodes   | 5 s      | 36             | ~3 min       |
| Scene readiness       | 15 s     | 120            | ~30 min      |
| Render finished       | 5 s      | 180            | ~15 min      |

If any loop times out the script exits non-zero. The two finalise loops
(`SCENE_POLL_*`, `RENDER_POLL_*`) live as top-of-file constants — bump them
if your environment is consistently slower.

---

## Exit behaviour

| Condition                                                          | Exit code |
| ------------------------------------------------------------------ | --------- |
| Success                                                            | 0         |
| Missing `e2e/.env.bb` or empty `YAKYAK_BB_PASSWORD`                | 1         |
| Token balance `< 2000` and either non-TTY or user answered `N`      | 1         |
| `--movie <id>` not present in the campaign                         | 1         |
| `--post-only` with no rendered movies in the campaign              | 1         |
| Any `sceneBurnSubtitle.status == "failed"`                         | 1         |
| Scene wait or render wait timed out                                | 1         |
| Network/jq parse failure on any required call                      | non-zero  |
| Individual `post-movie` 4xx (e.g. PFM 429)                         | **counted, not fatal** — final summary prints `N ok, M failed` |

---

## Running unattended (cron)

All three ports — `upload_to_yakyak.sh`, `.py`, `.js` — are designed to run
without a terminal. They detect the absence of a TTY (`[[ -t 0 ]]` / `sys.stdin.isatty()`
/ `process.stdin.isTTY`) and resolve every interactive prompt deterministically
instead of hanging. There are exactly **two gates**:

| Gate | On a TTY | Non-interactive (cron) |
| --- | --- | --- |
| Token balance `< 2000` | prompts "continue anyway?" | **aborts** with exit 1 |
| Social-post confirmation (only with `--post`) | prompts to confirm episode + networks | **refuses unless `--yes`/`-y`** (exit 1) |

So the rules for cron are:

- **Upload + render only** (no posting): no extra flags. It never blocks — but
  it *will* abort if the campaign owner's token balance is under 2000. Keep it
  topped up, or the run silently no-ops.
- **Upload + render + post**: you **must** pass `--yes`, otherwise it refuses to
  post and exits 1. That flag exists specifically for unattended runs.

### Environment

Auth is a Personal Access Token, not email/password. All three scripts read
`YAKYAK_BB_PAT` (a `yy_live_…` token) from `<repo>/e2e/.env.bb`, falling back to
the process environment. **The `e2e/.env.bb` file must exist** (it's resolved
relative to the script's own location, so cron's working directory doesn't
matter) — if it's missing the script exits 1 before doing anything. You can keep
the PAT in that file, or leave the file present-but-empty and inject
`YAKYAK_BB_PAT` via the environment.

Optional overrides: `YAKYAK_API_URL` (default `https://api.yakyak.ai`),
`YAKYAK_CDN_URL` (default `https://cdn.yakyak.ai`).

### Cron-environment gotchas (the environment, not the scripts)

cron runs with a bare `PATH`, no shell profile, and a different CWD. The scripts
handle CWD (paths are resolved relative to the script file), but you must handle:

1. **`PATH` / interpreter.** cron's `python3` / `node` may not be the one you use
   interactively (venv, nvm, Homebrew). Use absolute paths or set `PATH` in the
   crontab.
2. **`claude` CLI.** For prompt-kind shows, `showrunner/prepare.sh` (story
   generation — *hard* dependency, aborts without it) and the `--post` social-title
   step (*soft* — falls back to the first headline) shell out to `claude -p`. Make
   sure it's on cron's `PATH` if you generate stories in the same job. (Computed
   shows like Horoscopes need no model.)
3. **Per-language deps.** `.py` needs `yakyak-sdk` + `certifi` in the interpreter
   cron invokes; `.js` needs `node_modules` in `showrunner/`. (The `.sh` port
   only needs `curl` + `jq`.)
4. **Story freshness.** The picker uses the newest file matching the show's
   `STORY_GLOB`; run `showrunner/prepare.sh <showDir>` *before* the upload.
5. **Redirect output** to a log so the abort-on-low-tokens / abort-on-missing-`--yes`
   cases are visible.

### Example crontab

```cron
# Explicit PATH so python3/node/claude resolve under cron
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin

# 06:15 daily — prepare the story, then upload + render + post unattended.
# The && chain stops the run if prepare fails or the token gate aborts,
# so a stale/empty episode is never posted. SHOW points at the show dir.
15 6 * * * cd /Users/johan/Projects/121/repos/yakyak && \
  ./marketing/showrunner/prepare.sh marketing/BreakingBricksNews >> /tmp/bbn.log 2>&1 && \
  python3 ./marketing/showrunner/upload_to_yakyak.py --show marketing/BreakingBricksNews --post --yes >> /tmp/bbn.log 2>&1
```

Swap the last line for the port you prefer — all three accept the same flags and
the same `--show`:

```bash
./marketing/showrunner/upload_to_yakyak.sh  --show marketing/BreakingBricksNews --post --yes   # bash + curl + jq
python3 ./marketing/showrunner/upload_to_yakyak.py --show marketing/BreakingBricksNews --post --yes
node    ./marketing/showrunner/upload_to_yakyak.js --show marketing/BreakingBricksNews --post --yes
```

Drop `--post --yes` to upload + render only (review in the export page, then
`--post-only` by hand later). For a different show, point `--show` (and the
`prepare.sh` argument) at its directory, e.g. `marketing/Horoscopes`.

---

## Containerized runs (prebuilt Docker)

The cron gotchas above are almost all *environment drift* — wrong interpreter,
missing dep, absent `claude`, empty CA bundle on a fresh box. A prebuilt image
pins all of that once, so a run becomes a single reproducible `docker run`.

**These images now exist in the repo** — see
[`../../showrunner/`](../../showrunner/): `Dockerfile.py`, `Dockerfile.js`,
`Dockerfile.sh` (the three engine ports) and `Dockerfile.prepare` (adds the
`claude` CLI for prompt-kind shows like BBN). The
[`showrunner/README.md`](../../showrunner/README.md) is the canonical reference;
the essentials:

```bash
# Build from the REPO ROOT (Dockerfile COPY paths assume it):
docker build -f marketing/showrunner/Dockerfile.py -t yakyak/showrunner-py .

# Run: PAT via -e (never baked); stories mounted; --show selects the show.
docker run --rm -e YAKYAK_PAT \
  -v "$PWD/marketing/BreakingBricksNews/stories:/app/marketing/BreakingBricksNews/stories" \
  yakyak/showrunner-py --show marketing/BreakingBricksNews --post --yes
```

The image bakes the engine **and every `show.env`/prompt/compute**; only the PAT
and freshly-prepared stories come in at runtime. The empty `e2e/.env.bb` is baked
so the file-exists check passes; the real PAT arrives via `-e YAKYAK_PAT`.

### Scheduling the container

- **GitHub Actions** *(implemented)* — `.github/workflows/build-showrunner.yml`
  builds + pushes the images to ECR; `.github/workflows/run-shows.yml` runs a
  daily matrix of due shows (render-only by default, `post` opt-in). See
  [`showrunner/README.md`](../../showrunner/README.md#ci-github-actions).
- **Host cron / systemd timer** — wrap the `docker run` above; `&&`-chain a
  `prepare` run first (`--entrypoint marketing/showrunner/prepare.sh`).
- **AWS ECS Scheduled Task** (EventBridge) — fits the existing YakYak AWS
  footprint; PAT from Secrets Manager, image from the same ECR registry.

In every case the two non-interactive gates still apply: keep the token balance
≥ `MIN_TOKEN_BALANCE`, and pass `--yes` whenever `--post` is set.

---

## Related

- [`../../showrunner/README.md`](../../showrunner/README.md) — **canonical** engine
  reference: `show.env` keys, adding a show, Docker, CI.
- [`alternative_setups.md`](alternative_setups.md) — 10 other shows on this engine.
- [`how_it_works.md`](how_it_works.md) — end-to-end pipeline overview.
- [`posting_to_instagram.md`](posting_to_instagram.md) — Instagram-specific
  connection setup.
- [`posting_to_x.md`](posting_to_x.md) — X / Twitter-specific connection setup.
