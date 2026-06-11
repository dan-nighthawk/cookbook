# Forking: campaigns vs. movies (and why asset paths look "wrong")

Forking is how YakYak gives you an **instant, free** copy of something that already
exists — a whole show or a single episode — by copying the *record* and **re-pointing
at the already-rendered assets** instead of regenerating them. This doc explains the
two fork flavors, the one endpoint behind both, and the storage/identity consequence
that surprises people: a forked campaign's asset URLs keep the **source** campaign's id
baked into their paths. That is by design, not drift.

If you just want the recipe, see [`../show/showrunner/FORKING.md`](../show/showrunner/FORKING.md).
For the full entry-point map, see [`workflows.md`](./workflows.md). This doc is the *why*.

---

## TL;DR

- **Fork campaign** (web: the **New campaign → Fork** path, `/newCampaign`) deep-copies
  an **entire campaign** — settings, cast, soundtrack, and every episode/movie.
- **Fork movie** (web: the **IG grid**, `/ig`) copies **one single movie** off the grid.
- Both are the **same endpoint**, `POST /workflow/fork-campaign`. The only difference is
  whether you pass `sourceMovieId`:
  - **omit** `sourceMovieId` → whole campaign;
  - **include** `sourceMovieId` → just that one movie.
- A fork **reuses already-rendered assets** (portraits, voices, subtitles, soundtrack,
  rendered video). **Re-rendering is the expensive step, and a fork skips it** — so a
  fork is **instant and costs zero tokens**. We deliberately do *not* re-render on fork
  because rendering costs money.
- Because nothing is re-rendered, the copied assets keep their **original S3 keys**, and
  those keys embed the **campaign id that was live when they were rendered** — i.e. the
  *source* campaign, not the new fork. So `live campaign id ≠ the id segment in asset URLs`.
- Those keys are **content addresses**: they name where the immutable bytes already live,
  not who owns the record now. A fork references the same keys untouched — that's why it's
  free and instant.

---

## The two fork flavors

Both flavors are **structural copies**: a new owned record (new ids) whose generated
content is *referenced*, not recreated. They differ only in **scope**.

| | **Fork campaign** | **Fork movie** |
|---|---|---|
| Web entry point | **New campaign → Fork** (`/newCampaign`) | **IG grid** (`/ig`) — fork a single tile |
| API | `POST /workflow/fork-campaign` | `POST /workflow/fork-campaign` |
| Body | `{ userId, sourceCampaignId }` — **no** `sourceMovieId` | `{ userId, sourceCampaignId, sourceMovieId }` |
| What's copied | the **whole campaign**: settings (style, aspect ratio, animationType), the full **cast roster** (portraits/voices/subtitle styles), the **soundtrack**, and **all movies** | **one movie**, wrapped in a destination campaign so it's editable on its own |
| Mental model | "Give me this entire **show** as my own starting point" | "I like this one **video** — hand me an editable copy" |
| Typical use | Stand up a new show from a demo without paying setup (`setup_show.sh` alternative) | Grab a finished episode to add an intro / swap the soundtrack / post to social |

Response (both flavors): `201 { message, movieId, campaignId, campaign }`. Even a
single-movie fork returns a `campaignId` — every movie lives inside a campaign, so the
fork gives you a campaign to hold the copied movie.

> The course lessons use the **movie** flavor: they pass both `sourceCampaignId` and
> `sourceMovieId` to fork the tutorial's template movie, getting an instant, render-free
> movie to experiment on. See `course/02-hello-world`, `course/06-intro-clip`,
> `course/07-soundtrack`, `course/08-social-post`.

---

## Fork vs. the other entry points

YakYak has four ways to start (see `workflows.md`). Only forking reuses rendered output:

| Entry point | Endpoint | Generates assets? | Cost | When |
|---|---|---|---|---|
| **Fork campaign** | `fork-campaign` (no `sourceMovieId`) | **No** — reuses source's | **Free / instant** | You want an existing show's exact cast + look |
| **Fork movie** | `fork-campaign` (+ `sourceMovieId`) | **No** — reuses source's | **Free / instant** | You want one existing episode to edit |
| **New campaign** | `create-campaign` → `start-campaign` | **Yes** — from a prompt | 💸 paid | Brand-new cast/style from scratch |
| **Import campaign** | `import-campaign` (JSON from `export-campaign`) | **Yes** — regenerates cast/soundtrack | 💸 paid | Reproducible roster from a checked-in `campaign.import.json` (what `setup_show.sh` does) |

The middle path the showrunner recommends: run `setup_show.sh` (import + generate) **once**
to mint a canonical campaign, then **fork that** for free forever.

What a fork inherits — and the sharp edges:

- **Inherited:** cast portraits, voices, subtitle styles, soundtrack, rendered trailer,
  campaign settings, and (for a campaign fork) all episodes.
- **A fork inherits incompleteness.** The source must be fully rendered; if its portraits
  or soundtrack never finished, the fork starts equally unfinished.
- **`allowNewCharacters` is not copied** — it resets to the default. Patch it afterward
  (`update-campaign-settings`) if your show needs new faces per episode.
- **Forks are forced into `pro` mode.** Fine for uploading; the showrunner flips mode per
  run as needed.

---

## Why the asset paths keep the *source* campaign's id

This is the part that trips people up, and it falls straight out of "fork = copy the
record, reuse the renders."

### Anatomy of an asset key

Every rendered asset (movie, audio, poster) is an object in S3 with a key shaped like:

```
prd/ugc/<USER_ID>/<CAMPAIGN_SEG>/<MOVIE_SEG>/<kind>/<file>
         │            │              │
         │            │              └─ per-movie id (one per episode/render)
         │            └─ the campaign id that was LIVE WHEN THIS WAS RENDERED
         └─ account/user id
```

`<CAMPAIGN_SEG>` is **campaign-scoped render provenance**: it is the campaign id at the
moment the bytes were written. It is *not* a live foreign key you can look a campaign up
by — it's part of an immutable content address.

### What a fork does to it

1. Fork mints a **new campaign record** with a **new top-level `id`**.
2. Fork **does not re-render** (that's the whole point — rendering costs money).
3. So the new campaign **references the existing objects by their existing keys** — and
   those keys still carry the **source** campaign's id in `<CAMPAIGN_SEG>`.

Net result after any fork:

```
campaign.id            = <the new fork's id>        ← the live foreign key
asset URL CAMPAIGN_SEG = <the source campaign's id> ← frozen at render time
```

After *N* forks you can have *N* campaign records all legitimately serving a movie whose
URL still embeds the **original** campaign's id. Working as intended.

### Worked example (the cookbook's own shows)

The 8 `show/*/show.env` campaigns were re-minted (their top-level `id`s changed), but
their template movies were carried over un-re-rendered. Take Horoscopes / "Cosmic Brief":

```
live campaign id (new)    = 96491ebf-585b-4451-befa-73bdbd47cfb9   ← belongs in CAMPAIGN_ID
renderedMovieUrl segment  = …/f7d7cf1c…/956e3d49-…/b2a2f3b0-…/movies/….mp4
                                          └CAMPAIGN_SEG┘ └MOVIE_SEG┘
```

`956e3d49…` (the `CAMPAIGN_SEG`) is the *prior* campaign's id, frozen into the asset key.
The stale `show.env` files had `CAMPAIGN_ID="956e3d49…"` — i.e. they'd been set from an
**asset path**, which is exactly the value that breaks after a fork, because no campaign
record has `id == 956e3d49…` anymore.

---

## Asset paths are content addresses

An asset's S3 key names **where the bytes live**, not **which campaign owns the record
today**. Consequences:

- The object is **immutable** once written. A fork doesn't move or rewrite it — the fork
  just references the same key. That's why forking is free and instant.
- A forked campaign serving an asset whose `CAMPAIGN_SEG` is some *other* campaign's id is
  therefore normal and expected. **The path is a content address, not an ownership claim** —
  don't "fix" a path to match the live campaign id, and never derive a campaign id *from*
  a path.

---

## Practical rule for config (`show.env`, scripts, anything storing ids)

Keep the two kinds of identifier strictly separate:

- **`CAMPAIGN_ID` must be the live top-level campaign `.id`.** It's the foreign key the
  API and tooling resolve against — `get-campaign`, `create-new-season`, and
  `setup_show.sh`'s `select(.id == $id)`. A fork changes this; **update it after forking.**
- **Asset paths are content addresses — leave them alone across forks.**
  `SOUNDTRACK_AUDIO_PATH`, poster URLs, and movie URLs name objects in the shared bucket;
  the objects still exist after a fork, so the paths keep working untouched. Their
  embedded `CAMPAIGN_SEG` is *expected* to differ from the live `CAMPAIGN_ID` — do **not**
  "fix" a path to match the new id, and never derive `CAMPAIGN_ID` *from* a path.

> Rule of thumb: if a value is something you **look a campaign up by**, it's the live
> `.id`. If it's something you **fetch bytes from**, it's a path and its ids are frozen.

---

## See also

- [`workflows.md`](./workflows.md) — the four entry points and the full route map.
- [`../show/showrunner/FORKING.md`](../show/showrunner/FORKING.md) — step-by-step: fork a
  campaign instead of running `setup_show.sh`, then produce episodes.
- `course/02-hello-world`, `course/06-intro-clip`, `course/07-soundtrack`,
  `course/08-social-post` — runnable single-movie forks (sh / py / js).
