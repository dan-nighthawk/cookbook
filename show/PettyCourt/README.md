# PettyCourt

> A daily small-claims-TV sitcom: a real Reddit drama thread, fetched live, *paraphrased* into a SFW courtroom case, and presided over by Judge Justine Payne with a recurring roster of litigant archetypes. Eight scenes, ending on the verdict.

## What this show is

**Petty Court — Reddit/AITA Drama Reenactments** is one of the eight example
shows in the YakYak cookbook (see [`../README.md`](../README.md)). Each episode
takes the day's top post from a "drama" subreddit (r/AmItheAsshole and friends),
**paraphrases** it into a self-contained two-party dispute, recasts the real
people as a fixed roster of cartoon archetypes, and stages the whole thing as an
over-the-top daytime courtroom sitcom — gavel, faux-wood bench, reaction shots —
that ends on a screenshot-able verdict.

It is the cookbook's worked example of **live user-generated-content (UGC)
sourcing done safely**: the story is real and topical, but it is never reproduced
verbatim. It is transformed into something new, comedic, and copyright-safe before
a frame is rendered.

- **Sourcing:** Prompt / WebFetch + model (`PREPARE_KIND="prompt"`, `REQUIRES_MODEL="true"`)
- **Engine:** `py` · **Cadence:** `daily` · **Aspect ratio:** 9:16 (vertical)
- **Style:** Cartoon 3D · **Animation:** Kling (AI video generation)
- **Subtitle font:** Bangers, a distinct color per character

## What it demonstrates

- **Live UGC sourcing.** `prompt.md` drives `claude -p` to fetch the day's
  highest-upvoted posts from real drama subreddits via Reddit's public, no-key
  JSON — fresh, topical material every run with no baked corpus.
- **Transformative paraphrase (copyright-safe, never verbatim).** The Reddit text
  is *never* quoted. The prompt requires the model to paraphrase the dispute into
  its own words, change names/jobs/incidental details, and recast the parties as
  archetypes — keeping only the comedic *shape* of the conflict. This is treated
  as a legal/SFW requirement, not a stylistic nicety.
- **Virality pre-screen via upvotes.** The upvote (`score`) count *is* the
  built-in pre-screen: the model picks the most-upvoted SFW story, so the crowd
  has already validated that the drama is engaging before it's dramatized.
- **Distinct voices & a recurring cast.** A fixed roster (one Judge + five
  litigant archetypes) maps onto each day's two parties, each with its own
  ElevenLabs voice and its own Bangers subtitle color — recognizable continuity
  across episodes from an ever-changing source.

## How it works

### Story sourcing (`prompt.md`)

`prompt.md` is the head-writer brief handed to `claude -p`. Faithful summary of
what it does, in order:

1. **Fetch the source (WebFetch, one call per URL).** Reddit serves public,
   no-key JSON when you append `.json` to a listing. The prompt tries these
   top-of-day listings in order and uses the **first that returns usable posts**:
   - `r/AmItheAsshole/top.json?t=day&limit=15`
   - `r/AITAH/top.json?t=day&limit=15`
   - `r/pettyrevenge/top.json?t=day&limit=15`
   - `r/EntitledPeople/top.json?t=day&limit=15`

   For each post (`data.children[].data`) it reads `title`, `selftext` (body),
   `score` (upvotes), `num_comments`, `over_18`, and `link_flair_text` (the
   verdict flair, e.g. "Not the A-hole"). On rate-limit (HTTP 429/403) it first
   retries on the more lenient `old.reddit.com` host, then falls back to the
   free **pullpush.io** Reddit archive mirror (same fields, no key). If a fetch
   still fails it notes that in the Headlines block and proceeds with whatever it
   got — it must **never invent a Reddit story or fabricate an upvote count**.

2. **Pick & screen the case.** Choose the highest-`score` post that is clearly
   SFW (`over_18 == false`; skip anything sexual, abusive, self-harm, involving
   minors in distress, or graphic), has a self-contained two-party conflict, and
   is fun to dramatize. **The upvote count is the virality pre-screen** — prefer
   the most-upvoted SFW story. Identify the two parties and the petty stakes, and
   note the subreddit's verdict flair if present (it becomes the Judge's ruling).

3. **Transform, don't copy.** A stated legal/SFW requirement: **paraphrase** the
   story in the model's own words, recast the real people as the archetypes,
   change names/jobs/incidental details, and keep only the comedic shape of the
   dispute. **Never quote the Reddit text verbatim. No real names, no slurs,
   nothing explicit. Punch up, not down.**

4. **Stage it as a courtroom sitcom.** Exactly **8 scenes**. Scene 1: Judge
   Justine Payne gavels court into session and lays out the case. Scenes 2–7: the
   two best-fit archetypes testify, accuse, and escalate the pettiness to a
   comedic peak. Scene 8: the Judge delivers the verdict (using the subreddit's
   ruling where there was one) and bangs the gavel. Each scene is ~200 words of
   director-style visual prose plus **exactly one** 8–12-word spoken line
   attributed to that scene's leading character (which must be one of the cast,
   and the dialog line must not end in a period — `!`/`?` are fine).

5. **Save.** The model writes the story markdown via the Write tool to the
   `{{OUTPUT_FILE}}` path the engine passes in (it does not print the story to
   chat), then replies with just the absolute path. Output filenames match
   `STORY_GLOB="*_petty_court.md"` and land in [`stories/`](stories/).

### Cast & style

`campaign.import.json` carries the recurring cast and look (config only — no
rendered assets). `CAST_ALIASES` in `show.env` maps each full cast name to
**itself** (identity aliases), so the engine doesn't collapse e.g. "Judge Justine
Payne" down to "Judge"; multi-word names are listed first so they win the
substring match.

| Character | Role | Voice (ElevenLabs) | Subtitle color (Bangers) |
|-----------|------|--------------------|--------------------------|
| **Judge Justine Payne** — sharp-tongued small-claims judge; opens court (scene 1) & delivers the verdict (scene 8) | Guru | Sarah | `#FFD700` (gold) |
| **Marlene the Monster-in-Law** — immaculate, passive-aggressive overbearing in-law; casserole as a weapon | Antagonist | Dorothy | `#8E44AD` (purple) |
| **Trevor the Freeloader** — couch-surfing slacker; eats your food, pays no rent, victim in his own mind | Antagonist | Sam | `#2ECC40` (green) |
| **Bridezilla Bree** — wild-eyed bride/party diva; the day is all about her | Antagonist | Gigi | `#FF1493` (hot pink) |
| **Dex the Petty Ex** — smug, scheming ex; screenshots everything, returns your stuff slightly damaged | Antagonist | Antoni | `#00CED1` (teal) |
| **Reasonable Ray** — level-headed everyman, usually in the right (the "Not the Asshole") | Protagonist | Brian | `#1E90FF` (blue) |

Each episode uses the Judge plus the **2 archetypes that best fit** the day's two
parties (not all six). Style details from the campaign config:

| Setting | Value |
|---------|-------|
| `style` | Cartoon 3D — "colorful and bouncy 3D characters with exaggerated features, smooth surfaces, playful animations; family-friendly, vibrant palettes" |
| `aspectRatio` | `9:16` (vertical short-form) |
| `animationType` | `kling` |
| `subtitleMode` | `overlay`, font **Bangers**, per-character color (table above) |
| `imageQuality` / `mode` | `fast` / `pro` |
| `allowNewCharacters` | `false` — only the six fixed cast names may appear |
| `subtitleFont` | Bangers |

### Render & post

- **Engine:** `py` (`ENGINE="py"`). Story sourcing is `PREPARE_KIND="prompt"`,
  `REQUIRES_MODEL="true"` (CI needs `ANTHROPIC_API_KEY` + the `-claude` image).
- **Soundtrack:** one AI-composed track reused by every episode. `setup_show.sh`
  composes it once from `MUSIC_PROMPT` (an "upbeat daytime-TV courtroom sitcom
  theme … gavel hits, retro game-show energy") and writes the resulting
  `SOUNDTRACK_AUDIO_PATH` back into `show.env`. Mixed at `VOLUME="45"`.
- **Cadence:** `daily` — the source (drama subreddits) is effectively infinite.
- **Flags:** `ENABLED="false"` (flip to `true` after a local setup + first
  verified render) and `POST="false"` (render-only; set `true` to publish to
  social on scheduled runs — irreversible).

## Files in this directory

| File | Purpose |
|------|---------|
| [`show.env`](show.env) | Show configuration — campaign id, cast aliases, prepare kind, soundtrack, cadence, CI flags. See [Configuration](#configuration). |
| [`prompt.md`](prompt.md) | The head-writer brief for `claude -p`: which subreddits to fetch, the upvote selection, the transformative + SFW paraphrase rules, and the 8-scene courtroom structure. |
| [`campaign.import.json`](campaign.import.json) | One-time campaign import: the Judge + 5 litigant archetypes (descriptions, per-character ElevenLabs voices and Bangers subtitle colors) and the 9:16 / Cartoon-3D / Kling config. Carries config only — **no rendered assets**. Includes one sample movie ("Casserole Catastrophe", 8 scenes + a "Made with YakYak" outro card). |
| [`stories/`](stories/) | Generated story-markdown, one file per episode (`*_petty_court.md`), written by `prompt.md`. `.gitkeep` keeps the dir; sourced `.md` is stored inline (diffable), not LFS — see `.gitattributes`. |
| [`.gitattributes`](.gitattributes) | Overrides the repo-root LFS catch-all so this show's text (`.md`/`.json`/`.env`/`.txt`) is stored inline and diffable; binary brand assets (if added later) stay in LFS. |

## Configuration

Keys set in [`show.env`](show.env) (no secrets — the PAT and `ANTHROPIC_API_KEY`
come from the environment/CI):

| Key | Value | Notes |
|-----|-------|-------|
| `CAMPAIGN_ID` | `e98010e1-6fc0-4c1c-b0a0-770fc60e3339` | Target YakYak campaign. Leave empty and run `setup_show.sh` to import the campaign and fill this in. |
| `SOUNDTRACK_AUDIO_PATH` | `prd/ugc/…/…mp3` | One AI-composed track reused by every episode. Set manually to skip composition. |
| `MUSIC_PROMPT` | "Upbeat daytime-TV courtroom sitcom theme: bouncy walking bassline, jazzy muted-brass stabs, comedic woodblock and gavel hits, retro game-show energy …" | Mood for the one-time soundtrack compose. |
| `VOLUME` | `45` | Soundtrack mix level. |
| `MIN_TOKEN_BALANCE` | `2000` | Guard — skip the run if the account balance is below this. |
| `STORY_GLOB` | `*_petty_court.md` | Which files in `stories/` count as episodes. |
| `STORY_SUFFIX` | `_petty_court.md` | Suffix `prepare.sh` appends to the UTC timestamp when writing a story. |
| `CAST_ALIASES` | `Judge Justine Payne=Judge Justine Payne,…` (6 identity aliases) | Maps each full cast name to itself so multi-word names aren't collapsed to first names. |
| `PREPARE_KIND` | `prompt` | Story comes from `prompt.md` driven by `claude -p` (WebFetch + Write). |
| `REQUIRES_MODEL` | `true` | CI needs `ANTHROPIC_API_KEY` + the `-claude` engine image. |
| `CADENCE` | `daily` | Near-daily; source is effectively infinite. |
| `ENGINE` | `py` | Which port CI runs for this show. |
| `ENABLED` | `false` | Disabled until you flip `true` after a local setup + first verified render. |
| `POST` | `false` | Render-only by default; `true` publishes to social on scheduled runs (irreversible). |

## Run it

First-time campaign setup (imports `campaign.import.json`, generates the 6 cast
portraits, composes the soundtrack, bootstraps season 1, and fills in
`CAMPAIGN_ID` / `SOUNDTRACK_AUDIO_PATH`):

```sh
YAKYAK_PAT=yy_live_... ./showrunner/setup_show.sh PettyCourt
```

Then, per episode — source the story, then upload + render with the `py` port:

```sh
# 1) source the day's story (prompt-kind → needs `claude` / ANTHROPIC_API_KEY)
./showrunner/prepare.sh PettyCourt

# 2) upload + render (render-only by default)
./showrunner/upload_to_yakyak.py --show PettyCourt

# …or upload + render + publish to social (irreversible)
./showrunner/upload_to_yakyak.py --show PettyCourt --post --yes
```

CI runs the same steps via the **Render Shows** workflow (generates + renders due
shows, render-only by default) and **Post Episode** (publishes one already-rendered
episode). See [`../showrunner/README.md`](../showrunner/README.md) for the full key
reference and engine details.

## Notes & gotchas

- **Transformative is mandatory, not optional.** The whole show only works because
  the source is **paraphrased and recast**, never reproduced verbatim. The prompt
  treats this as a legal/SFW requirement: change names, jobs, and incidental
  details; keep only the comedic shape; no real names; no quoting the Reddit text.
  If you adapt this show, keep that rule intact.
- **SFW screening.** Stories must be `over_18 == false` and free of sexual,
  abusive, self-harm, minors-in-distress, or graphic content. The model "punches
  up, not down."
- **Live Reddit dependency.** Sourcing depends on Reddit's public JSON, which
  rate-limits (429/403) unpredictably. The prompt degrades gracefully: retry on
  `old.reddit.com`, then fall back to the pullpush.io archive mirror. If everything
  fails it notes the gap and proceeds with what it has — it must **never fabricate**
  a story or an upvote count. Because the source is live, episodes are **not
  reproducible** run-to-run (unlike the computed shows).
- **Upvotes = virality pre-screen.** Picking the highest-`score` SFW post is the
  whole quality filter; there's no separate ranking step.
- **Animation.** Renders with **Kling** (AI video generation); while refining the
  channel you can switch `animationType` to **Ken Burns** — a pan/zoom over the
  still — which renders **faster and cheaper**, then switch back to Kling for the
  finished look.
- **Disabled by default.** `ENABLED="false"` and `POST="false"` — flip these only
  after a local setup and a first verified render.

## Reference

- Show gallery & sourcing model: [`../README.md`](../README.md)
- Showrunner engine & full config key reference: [`../showrunner/README.md`](../showrunner/README.md)
- Pipeline (campaign → movie → scene), forking, debugging: [`../../docs/`](../../docs/)
- Product: https://yakyak.ai/
- API docs: https://api.yakyak.ai/api/docs
