# BreakingBricksNews

> Flagship **satirical brick-built news** — the day's real Middle East headlines, restaged as a dark-comedy newscast in a LEGO/brickfilm world and auto-posted to social.

## What this show is

BreakingBricksNews ("BBN") is the cookbook's flagship example show: a daily, short-form
**satirical news channel** rendered entirely in a playful brick (LEGO/brickfilm) art
style. Each episode takes that day's **real, current headlines** about the Middle East
and reweaves 3–6 of them into a single tongue-in-cheek narrative arc — a ten-scene
"newscast" that opens cold with a field reporter and signs off with the same reporter.

The conceit is a fictional news desk, **Breaking Bricks News**, anchored by recurring
field reporter **Bob Brikko** ("our fearless field reporter… dry, deadpan under fire"),
who reports history while standing in the middle of it. Around Bob, a small recurring
cast of public figures plays out the day's events as brick characters: **Donald Trump**,
**Benjamin Netanyahu**, **Mojtaba Khamenei** (collapsed together with Khamenei in the
cast map), and an unnamed **Israeli Pilot** ("The Pilot").

The output of each run is one **story markdown file** in [`stories/`](stories/) (named
`<UTC-timestamp>_latest_update.md`) describing the headlines used plus ten scenes — each
scene with a leading character, exactly one short spoken dialog line, and ~200 words of
director's-brief prose. The showrunner turns that story into a rendered, soundtracked,
subtitled brick-world video and (for this show) posts it to social.

## What it demonstrates

As one of eight example shows, BBN is the cookbook's worked example of:

- **Live "Prompt / WebFetch" sourcing** — `PREPARE_KIND="prompt"`, `REQUIRES_MODEL="true"`.
  Unlike the *computed* or *extracted* shows, BBN's story is written fresh each run by
  `claude -p`, which uses **WebFetch** to pull genuinely live headlines and **Write** to
  emit the story file. No headlines are baked into the repo.
- **A recurring, fully-specified cast** — named characters with pinned voices, per-character
  subtitle colors, reference images, and a fixed cast map (`CAST_ALIASES`), so episodes
  stay visually and tonally consistent day to day.
- **Auto-posting on auto-pilot** — BBN is the show currently wired for live publishing
  (`ENABLED="true"`, `POST="true"`), so it demonstrates the full **source → render → post**
  loop end to end, not just render-only.

## How it works

### Story sourcing

Sourcing is driven by [`prompt.md`](prompt.md), which `prepare.sh` feeds to `claude -p`.
The prompt casts the model as the head writer of "Breaking Bricks News" and walks four
steps:

1. **Fetch the news** — one `WebFetch` call per URL, against three server-rendered,
   no-JS sources: the **BBC** Middle East RSS feed (`feeds.bbci.co.uk/news/world/middle_east/rss.xml`),
   **CNN Lite** (`lite.cnn.com`, using only `/middleeast/` links and the date baked into
   each URL), and the **Al Jazeera** Middle East page. For each it extracts top headlines,
   timestamps, and a one-line summary. Only items from the **past 24 hours** are kept; if a
   site blocks the fetch, the model notes it and proceeds with what it has.
2. **Pick the threads** — choose 3–6 real developments that weave into a single narrative
   arc, preferring items that touch more than one cast member.
3. **Write the story** — a ten-scene script. Only the five cast members may speak, and the
   *leading character* of each scene must be one of them. **Bob Brikko must lead Scene 1
   (cold open) and Scene 10 (sign-off).** Each scene gets ~200 words of visual/atmosphere
   prose written like a camera-op brief, plus **exactly one** 8–12-word dialog line for
   the leading character (no trailing period). Tone is dark comedy driven by real headline
   beats — "punch up, not down," no slapstick, no slurs.
4. **Save the result** — `Write` the markdown to the exact `{{OUTPUT_FILE}}` path (the
   showrunner fills in `{{OUTPUT_FILE}}` and `{{TIMESTAMP}}`), then reply with just that
   path. The file follows a fixed shape: a header with generated-UTC + sources, a
   "Headlines we drew from" bullet list, and `## Scene N` blocks with **Leading character**
   and **Dialog** fields.

The committed files in [`stories/`](stories/) (27 of them at time of writing, e.g.
`20260610T002208Z_latest_update.md`) are exactly these generated outputs — useful as
real reference samples of what the prompt produces.

### Cast & style

Defined by `CAST_ALIASES` in [`show.env`](show.env) plus the campaign's cast/style in
[`campaign.import.json`](campaign.import.json) (summarized here — the JSON itself holds
the full per-character descriptions, screenplay, and scene blobs and should not be pasted):

- **Cast map** — `Bob=Bob, Trump=Trump, Netanyahu=Netanyahu, Mojtaba=Mojtaba,
  Khamenei=Mojtaba, Pilot=Pilot`. Note both `Mojtaba` and `Khamenei` collapse to the
  single screenplay alias **Mojtaba**; matching is by leading-character name substring in
  priority order.
- **Voices** (pinned per character):

  | Character | Voice |
  |-----------|-------|
  | Bob Brikko | Drew |
  | Donald Trump | Eric |
  | Benjamin Netanyahu | Callum |
  | Mojtaba Khamenei | Clyde |
  | Israeli Pilot | Arnold |

- **Subtitles** — all characters use the **Anton** font with `subtitleMode: overlay`, but
  each gets a distinct color so dialog is attributable at a glance:

  | Character | Subtitle color |
  |-----------|----------------|
  | Bob Brikko | `#366b00` (green) |
  | Donald Trump | `#8b7e27` (gold) |
  | Benjamin Netanyahu | `#7977da` (indigo) |
  | Mojtaba Khamenei | `#7a7a7a` (gray) |
  | Israeli Pilot | `#69c4f2` (light blue) |

- **Art style** — `LEGO / Brickfilm`: "Playful brick-based animation with blocky characters
  and colorful plastic aesthetics… clean geometric forms and vibrant staging."
- **Render shape** — `aspectRatio: 9:16` (vertical/short-form), `animationType: kling`,
  `imageQuality: fast`, `mode: pro`, `allowNewCharacters: false` (the cast is closed — no
  new characters invented per episode), `skipSoundtrack: false`. Renders with **Kling**
  (AI video generation); while refining the channel you can switch `animationType` to
  **Ken Burns** — a pan/zoom over the still — which renders **faster and cheaper**, then
  switch back to Kling for the finished look.

Each of the five cast members also carries a reference image and a detailed visual
description in `campaign.import.json` so the brick character renders consistently across
episodes.

### Render & post

- **Engine** — `ENGINE="py"` (the Python port of the uploader; all three ports produce
  identical results).
- **Soundtrack** — `SOUNDTRACK_AUDIO_PATH` points at the BBN intro track, an opaque CDN
  asset path that originates on the "Power Struggle" sibling episode and is reused by the
  render from the CDN. A local copy of that track lives at
  [`assets/2c53f283-6b9f-482a-a8f0-a37ba7b5a194.mp3`](assets/). `VOLUME="45"` sets the
  soundtrack mix level.
- **Cadence** — `CADENCE="daily"`; `plan_due_shows.sh` uses this to schedule the day's run.
- **Sourcing flags** — `PREPARE_KIND="prompt"` + `REQUIRES_MODEL="true"` (CI needs
  `ANTHROPIC_API_KEY` and the `-claude` image).
- **Posting** — `ENABLED="true"` and `POST="true"`. This is the one example show wired to
  **publish to social on scheduled runs** (irreversible); other shows default to
  render-only. `MIN_TOKEN_BALANCE="2000"` guards against running with insufficient credits.

## Files in this directory

| Path | What it is |
|------|------------|
| [`README.md`](README.md) | This file. |
| [`show.env`](show.env) | The show's config — campaign id, cast map, sourcing/render/post flags. Consumed by the showrunner uploader. |
| [`prompt.md`](prompt.md) | The `claude -p` prompt that fetches live headlines and writes the day's story file. |
| [`campaign.import.json`](campaign.import.json) | Exported YakYak campaign: style, cast (descriptions, voices, subtitle colors, images), and a sample movie/screenplay. Used to (re)create the campaign. |
| [`stories/`](stories/) | Generated story markdown files (`<UTC-ts>_latest_update.md`), one per run — real outputs of `prompt.md`. |
| [`assets/`](assets/) | Binary brand assets — currently the BBN intro soundtrack mp3 referenced by `SOUNDTRACK_AUDIO_PATH`. |
| [`.gitattributes`](.gitattributes) | Per-subtree override: keeps text/source (`.md/.sh/.py/.js/.json/.env`) out of Git LFS and diffable, while binary assets (`.mp3`, images, video) stay in LFS. |

## Configuration

Meaningful keys from [`show.env`](show.env) (secrets/tokens omitted):

| Key | Value | Meaning |
|-----|-------|---------|
| `CAMPAIGN_ID` | `a7e7b9c5-0959-41a0-9176-509a3b197775` | The BBN production campaign episodes are added to. |
| `SOUNDTRACK_AUDIO_PATH` | *(opaque CDN path)* | audioPath of the BBN intro track; set on the new episode so the render reuses it from the CDN. |
| `VOLUME` | `45` | Soundtrack mix volume. |
| `MIN_TOKEN_BALANCE` | `2000` | Refuse to run below this credit balance. |
| `STORY_GLOB` | `*_latest_update.md` | Which story files the uploader picks up. |
| `STORY_SUFFIX` | `_latest_update.md` | Suffix `prepare.sh` writes (`<UTC-ts><suffix>`); kept consistent with `STORY_GLOB`. |
| `CAST_ALIASES` | `Bob=Bob,Trump=Trump,Netanyahu=Netanyahu,Mojtaba=Mojtaba,Khamenei=Mojtaba,Pilot=Pilot` | Leading-character name → screenplay alias, priority order (Khamenei collapses to Mojtaba). |
| `PREPARE_KIND` | `prompt` | Source each episode via `prompt.md` + `claude -p`. |
| `REQUIRES_MODEL` | `true` | Sourcing needs a model (`ANTHROPIC_API_KEY` / `-claude` image in CI). |
| `CADENCE` | `daily` | Scheduling cadence. |
| `ENGINE` | `py` | Which uploader port CI runs. |
| `ENABLED` | `true` | Include in scheduled runs. |
| `POST` | `true` | Publish to social on scheduled runs (irreversible). |

The auth token is a single shared PAT, read from `YAKYAK_PAT` by default (with a legacy
`YAKYAK_BB_PAT` fallback); `PAT_ENV_KEY` can pin a different env var name but is left
commented out.

## Run it

From the repo, with the shared engine in `show/showrunner/`. The engine port matches
`ENGINE="py"`:

```sh
# 1. One-time: (re)create the campaign from campaign.import.json
YAKYAK_PAT=yy_live_... ./show/showrunner/setup_show.sh show/BreakingBricksNews

# 2. Source the day's story (prompt-kind → needs the `claude` CLI + ANTHROPIC_API_KEY)
./show/showrunner/prepare.sh show/BreakingBricksNews

# 3. Render, and post (this show is post-enabled)
YAKYAK_PAT=yy_live_... ./show/showrunner/upload_to_yakyak.py --show show/BreakingBricksNews

# Render-only (do NOT publish) while iterating: omit --post / don't pass --yes
./show/showrunner/upload_to_yakyak.py --show show/BreakingBricksNews
```

The `js` and `sh` ports (`upload_to_yakyak.js`, `upload_to_yakyak.sh`) behave identically
if you prefer them. See [`../showrunner/README.md`](../showrunner/README.md) for the full
flag reference (including `--post` / `--yes` posting semantics).

## Notes & gotchas

- **This show posts for real.** `POST="true"` + `ENABLED="true"` means scheduled runs
  publish to social and that is irreversible. When testing locally, run render-only (don't
  pass the post/`--yes` flags) until you're sure.
- **Live data, non-reproducible.** Because the story comes from real headlines fetched at
  run time, each run differs and a run can't be reproduced offline. CI requires both
  `ANTHROPIC_API_KEY` and network access; if a source blocks the WebFetch the prompt
  proceeds with the remaining sources rather than failing.
- **The cast is closed.** `allowNewCharacters: false` and the fixed `CAST_ALIASES` mean
  only the five named characters may appear/speak; the prompt enforces the same rule. Bob
  Brikko is hard-pinned to lead the cold open (Scene 1) and the sign-off (Scene 10).
- **`Khamenei` aliases to `Mojtaba`.** The cast map intentionally points the subject at
  Mojtaba Khamenei (the Supreme Leader's son), not Ali — keep that in mind when reading
  generated stories.
- **Soundtrack is an opaque pinned asset.** `SOUNDTRACK_AUDIO_PATH` is a CDN path borrowed
  from a sibling episode; the local `assets/*.mp3` is a copy. Don't treat the path as
  editable text — it pins a specific uploaded track.
- **LFS split.** The local `.gitattributes` guards against any repo-wide `filter=lfs`
  catch-all so source/text stays diffable inline and only true binaries (mp3, images,
  video) go to LFS. A clone without git-lfs still reads all the source correctly.

## Reference

- Shows overview: [`../README.md`](../README.md)
- Showrunner config & engine: [`../showrunner/README.md`](../showrunner/README.md)
- Pipeline & model docs: [`../../docs/`](../../docs/)
- Product: https://yakyak.ai/
- API docs: https://api.yakyak.ai/api/docs
