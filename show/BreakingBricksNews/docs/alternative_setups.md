# Alternative Setups — 10 Viral Variations on the BBN Engine

Breaking Bricks News is just **one configuration** of a very general machine.
The engine does only three things:

1. A **`prepare_*` step** writes a story-markdown file (sourcing + creative).
2. **`upload_to_yakyak.*`** turns that file into a movie (cast, scenes, soundtrack, render).
3. A **schedule** repeats it (cron / container — see [`yakyak_upload_usage.md`](yakyak_upload_usage.md)).

Everything that makes BBN *BBN* — Middle-East news, the Bob Brikko anchor, the
dark-comedy tone — lives in (1) and in the campaign's cast/style. Swap the source,
the cast, the style and the cadence and you have a completely different show on
the same rails. This document gives **10 totally different shows**, each chosen
for proven, durable online demand, and each fully specified across the five levers
below. The script changes are minimal; the *creative configuration* is the product.

> **The contract every variation must honor.** Whatever the source, the
> `prepare_*` step must emit Markdown with: a `## Headlines we drew from:` block
> (becomes the social caption) and N × `## Scene M — <title>` sections, each with
> `**Leading character:** <name>`, `**Dialog:** "<one line>"`, then a prose
> paragraph (the visual brief). `storyToDescription()` collapses these into the
> `set-movie-metadata` payload; `gen-movie-screenplay` does the rest. See
> [`how_it_works.md`](how_it_works.md) and `../../showrunner/story-format.js`. Keep
> dialog lines free of trailing periods (`!`/`?` are fine).

## The five levers

| Lever | What it controls | Where you set it |
| --- | --- | --- |
| **Input / sourcing** | where the day's content comes from | the show dir's `compute.*` or `prompt.md` (the only real code per show), run by `showrunner/prepare.sh` |
| **Cast mixture** | who appears, their look/voice/subtitle style | campaign cast + custom-cast roster (`movie_custom_cast`); per-scene `**Leading character:**` |
| **Lifecycle** | how cast/format *evolve* across episodes | the prepare step's memory of prior episodes + scheduled config swaps |
| **Style / animation** | art style, motion (Ken Burns vs Kling), pacing | campaign style picker; Kling vs Ken Burns; scene count |
| **Aspect & sound** | 9:16 / 1:1 / 16:9, soundtrack, volume | campaign aspect ratio; `--soundtrack`, `--volume` |

Four sourcing *archetypes* recur below — **WebFetch** (live external data),
**Computed** (deterministic from date/almanac/math), **Randomized** (seeded draw),
**Extracted** (public-domain books/corpora). Mixing them is encouraged.

---

## 1. "Cosmic Brief" — Weekly Horoscopes (Computed)

**Viral hook.** Astrology is one of the highest-engagement evergreen verticals on
TikTok/Reels/Shorts; people watch *their own sign* and tag friends by sign. Built-in
12-way shareability every single week.

**Input / sourcing.** *Computed.* The prepare step takes the ISO week + a planetary
almanac (ephemeris table baked into the repo, or a free astronomy API via WebFetch
for transits) and deterministically derives a one-line forecast per sign. No model
needed for the data; the LLM only dramatizes it into a scene. Deterministic input =
reproducible, on-brand, zero source-licensing risk.

**Cast & evolution.** Twelve recurring **zodiac avatars** (Aries the hothead, Virgo
the perfectionist, etc.) as a fixed ensemble — the recurring cast is the retention
engine ("where's my Scorpio?"). Each weekly episode = 12 scenes, one per sign, same
characters, new predicaments. **Lifecycle:** rotate which sign opens/closes by the
Moon sign of the week; introduce a 13th "Ophiuchus" wildcard during sweeps weeks for
a controversy spike.

**Style / animation.** Mystical, painterly celestial style; slow **Ken Burns** drift
over starfields and tarot-deck-style portraits suits the contemplative tone. Deep
indigo/gold palette, per-sign accent color in the subtitle styling.

**Aspect & sound.** 9:16 vertical; ambient/cosmic pad soundtrack low (`--volume 30`)
so the voice carries the "reading."

**Cadence.** Weekly (Sunday night for the week ahead). One campaign, 12-scene movies.

```markdown
## Scene 4 — Cancer
**Leading character:** Cancer the Caretaker
**Dialog:** "Mercury says set a boundary; you'll apologize for it by Thursday"
A moonlit kitchen, Cancer hovering over three simmering pots that aren't theirs...
```

---

## 2. "Lucky Day" — Feng Shui & BaZi Almanac (Computed)

**Viral hook.** Enormous Chinese-diaspora and wellness audiences; daily-luck and
"auspicious dates" content travels on WeChat/TikTok/Reels and screenshots well.
Saveable + shareable ("don't sign anything today!").

**Input / sourcing.** *Computed.* Derive the day's element, animal, and clash from
the Chinese sexagenary calendar (a pure date→cycle calculation) plus a Flying Stars
month grid. The prepare step turns "Day clashes with Rat, favorable for water
element, avoid south" into scene briefs. Fully deterministic; no external calls.

**Cast & evolution.** The **12 Chinese zodiac animals** as a recurring troupe, plus
a calm **Feng Shui Master** anchor who frames each day. **Lifecycle:** the animal
"of the year" gets promoted to co-host for that lunar year, then steps down at New
Year — a built-in annual cast rotation that rewards long-term followers.

**Style / animation.** Clean ink-wash / modern-minimal style; gentle parallax
**Ken Burns**. Red/gold for auspicious beats, muted grey for warnings — encode luck
in color.

**Aspect & sound.** 1:1 or 9:16; guzheng/lo-fi blend, mid volume.

**Cadence.** Daily (short, 3–5 scenes) — high frequency is the point; perfect for
the cron/container scheduler.

---

## 3. "Sun Tzu, Today" — Art of War / Book of Five Rings (Extracted)

**Viral hook.** "Ancient strategy applied to modern life" is a monster niche
(career, dating, gym, business). Quote-card culture + the gravitas of a real text =
high saves and stitch-bait.

**Input / sourcing.** *Extracted.* Both texts are **public domain**. The prepare step
walks the corpus one verse/passage per episode (a cursor stored alongside the show so
it advances and never repeats), then asks the model to stage that maxim as a modern
micro-drama. Source is fixed and finite → a guaranteed multi-month content runway
from a single file.

**Cast & evolution.** A timeless **Strategist** (Sun Tzu / Musashi as a stylized
mentor) plus a rotating modern **protagonist** who faces a relatable dilemma (toxic
boss, bidding war, breakup) and applies the verse. **Lifecycle:** run it as a serial —
the same protagonist levels up across episodes (apprentice → master), or alternate
Art of War "seasons" with Book of Five Rings "seasons" for a built-in format refresh.

**Style / animation.** Cinematic chiaroscuro; ink-and-steel. **Kling animation** (not
Ken Burns) sells the duel/confrontation beats — motion matters here.

**Aspect & sound.** 9:16; taiko/percussion sting on the maxim reveal, then silence.

**Cadence.** 3×/week. Each ep ends on the verse as a caption card for screenshotting.

---

## 4. "You Decide" — Branching RPG / Choose-Your-Own-Adventure (Randomized + Audience)

**Viral hook.** Interactive, comment-driven serialization is the strongest *retention*
format on socials — viewers return for "what happens next" and the comments *are* the
algorithm. Cliffhangers compound.

**Input / sourcing.** *Randomized + extracted.* Model the story as a graph (hand-authored
or lifted from public-domain gamebook structures). Each episode ends on a 2-choice
fork. The next prepare run reads the **top-voted comment / poll result** (WebFetch the
social post's engagement, or a seeded random draw if you want it autonomous) and walks
that branch. The path is emergent.

**Cast & evolution.** A core **party** of adventurers whose fate is audience-decided —
**characters can die, defect, or be replaced** depending on the chosen branch. This is
the purest "cast changes during the life of the campaign" example: the roster at
episode 20 is a direct function of crowd choices at episodes 1–19.

**Style / animation.** Painterly fantasy or comic-panel style; **Kling** for action
forks, Ken Burns for dialogue forks. Branch-dependent palette shifts (the "dark path"
literally darkens).

**Aspect & sound.** 9:16; adaptive score (tense vs heroic) chosen per branch via
`--soundtrack`.

**Cadence.** 2×/week with a 24h voting window between. The schedule must read results
*before* generating — a perfect use of the chained cron/container job.

---

## 5. "Reality Olympus" — Greek Myth / Shakespeare as Reality TV (Extracted)

**Viral hook.** "Classic story but it's a reality show / group chat" is a proven
remix format. The drama is pre-built and timeless; the comedy is the anachronism.

**Input / sourcing.** *Extracted.* Public-domain mythology (Bulfinch, Hesiod) and the
Shakespeare canon. The prepare step adapts one episode of a myth/play into a
confessional-cam reality beat ("Zeus, talk us through what happened with the swan").
Finite, curated, endlessly meme-able source.

**Cast & evolution.** A large recurring **pantheon/troupe** with reality-TV archetypes
(the villain, the messy one, the wholesome one). **Lifecycle:** season-based — Season 1
"Olympus", Season 2 "Trojan War" (cast culled by who "dies"), Season 3 "Shakespeare
crossover." Eliminations and crossovers keep the roster fresh and dramatic.

**Style / animation.** Glossy reality-TV-meets-Renaissance; talking-head **Ken Burns**
for confessionals, **Kling** for the mythic action cutaways.

**Aspect & sound.** 9:16; reality-TV stingers and "confessional" pads.

**Cadence.** Weekly episodic; bracket-style eliminations for engagement spikes.

---

## 6. "Market Mayhem" — Crypto & Markets Daily (WebFetch + Computed)

**Viral hook.** FinTok / crypto Twitter is rabid and *daily*. Personifying the market's
mood ("Bitcoin had a day") is endlessly clippable, and volatility guarantees fresh
drama for free.

**Input / sourcing.** *WebFetch + Computed.* Pull the day's closes/volatility (free
price endpoints), compute movers and a fear/greed read, then dramatize. The data is
the plot — no two days repeat, and big-move days self-promote.

**Cast & evolution.** Personified assets as a recurring cast — **Bitcoin** (the smug
veteran), **a memecoin** (the chaos gremlin), **the Fed** (the disapproving parent),
**Gold** (the boomer). **Lifecycle:** the cast rotates with the market — a coin that
moons gets a glow-up; one that rugs is written out; new entrants debut on listing-day
spikes. The roster literally tracks reality.

**Style / animation.** Bloomberg-terminal-meets-cartoon; punchy **Kling** for green/red
candle "battles." Green/red is the entire color language.

**Aspect & sound.** 9:16 + 1:1 cross-post; tense electronic, volume scaled to the day's
volatility.

**Cadence.** Daily at market close (cron) — the flagship case for the scheduled container.

---

## 7. "On This Day" — Historical Reenactment (Computed + Extracted)

**Viral hook.** "Today in history" is a perennial Shorts/Reels staple with built-in
daily novelty and strong search/SEO pull. Educational + dramatic = high completion.

**Input / sourcing.** *Computed (date) + Extracted (public-domain history).* The prepare
step keys off today's calendar date, selects an anniversary, and stages the event as a
dramatized scene from public-domain accounts. Date-driven → infinite, self-refreshing,
never the same twice.

**Cast & evolution.** Episodic historical figures (different cast every day), unified by
a single recurring **Narrator/Time-Traveler** host who provides continuity and brand.
**Lifecycle:** themed weeks (Inventors week, Disasters week) swap the host's costume and
the visual style on a schedule — config-driven seasonal variety with no code change.

**Style / animation.** Sepia/archival → colorized; **Ken Burns** over period imagery
nails the documentary feel, with **Kling** reserved for the dramatic centerpiece.

**Aspect & sound.** 16:9 *and* 9:16 (history performs on YouTube too); orchestral score.

**Cadence.** Daily.

---

## 8. "Daily Pull" — Tarot / Oracle Card (Randomized)

**Viral hook.** "Pick a card" / daily-pull content is massively interactive and
loops well — viewers self-select and return daily. Pure ritual = pure habit.

**Input / sourcing.** *Randomized (seeded).* Draw 1–3 cards from the 78-card deck with a
date-seeded RNG (reproducible, auditable, and you can guarantee no repeats within a
window). The card *is* the prompt; the model writes the reading as a scene.

**Cast & evolution.** A recurring **Reader/mystic** host plus the **Major Arcana as a
recurring character universe** (The Fool, Death, The Tower as personalities who recur
when drawn). **Lifecycle:** "pick a pile" format splits each episode into 3 parallel
mini-readings (3 sub-casts) — and you can introduce a themed deck (e.g. a seasonal
Halloween deck) to refresh the whole look on schedule.

**Style / animation.** Ornate art-nouveau card art; candle-lit **Ken Burns**, card-flip
transitions. Per-card accent colors.

**Aspect & sound.** 9:16; mystical ASMR-leaning pad, low volume.

**Cadence.** Daily.

---

## 9. "Petty Court" — Reddit/AITA Drama Reenactments (WebFetch)

**Viral hook.** "Reddit story narrated/acted" is one of the single most-watched
short-form formats in existence (AITA, revenge, relationship drama). Endless free,
pre-validated-by-upvotes source material.

**Input / sourcing.** *WebFetch.* Pull top posts from drama subreddits via public JSON,
filter by score, and dramatize (paraphrased to avoid lifting text verbatim — keep it
transformative and SFW). The upvote count *is* your virality pre-screen.

**Cast & evolution.** A recurring **Judge/host** ("Petty Court is now in session") plus
episodic plaintiffs/defendants. **Lifecycle:** recurring "repeat offender" character
archetypes (the overbearing MIL, the freeloading roommate) become running gags the
audience anticipates; a monthly "Hall of Shame" clip-show recombines past casts.

**Style / animation.** Courtroom-cartoon / sitcom style; **Ken Burns** on reaction
shots, comedic zoom punches. Bold, high-contrast.

**Aspect & sound.** 9:16; sitcom stings, gavel SFX.

**Cadence.** Daily/near-daily — source is effectively infinite.

---

## 10. "Versus" — Tournament Bracket (Computed + Audience)

**Viral hook.** Bracket/"who would win" content weaponizes tribalism and FOMO —
audiences vote, defend their pick, and return to see if it survived. Single-elimination
creates a finite, bingeable arc with a finale payoff.

**Input / sourcing.** *Computed + Audience.* Seed a 16/32-entrant bracket (anything with
fandom: snacks, cities, fictional fighters, decades, programming languages). Each episode
is one matchup; the winner is decided by the prior post's poll/engagement (WebFetch) or a
weighted random if autonomous. The bracket state is the show's memory.

**Cast & evolution.** The **bracket entrants are the cast, and it shrinks every episode** —
the most literal "cast changes over the campaign's life." Round 1 has 32 personalities;
the finale has 2. A constant **commentator** duo provides continuity. Eliminated fan
favorites can return for a "loser's bracket" spin-off campaign.

**Style / animation.** Sports-broadcast / fighting-game aesthetic; **Kling** for the
clash, slow-mo replays. Each entrant gets a signature color carried in subtitles.

**Aspect & sound.** 9:16; hype/sports-arena soundtrack, swelling toward the finale.

**Cadence.** Daily during a "season"; each bracket = one self-contained campaign that
ends, then a new bracket (new theme) begins — natural restart points for the algorithm.

---

## Cross-cutting patterns

**Sourcing archetype → reliability.**

| Archetype | Examples here | Pros | Watch out for |
| --- | --- | --- | --- |
| WebFetch (live) | News (BBN), Markets, Reddit, Sports | always fresh, self-promoting | source HTML/API drift; rate limits; SFW/IP filtering |
| Computed (deterministic) | Horoscope, Feng Shui, On-This-Day, Tarot seed | reproducible, zero licensing, offline | needs a correct almanac/algorithm once |
| Randomized (seeded) | Tarot, Branching, Versus tiebreak | endless novelty, fair/auditable | seed must be logged for reproducibility |
| Extracted (books) | Sun Tzu, Myth/Shakespeare, History | gravitas, finite runway, pre-loved | **public domain only** — track a cursor to avoid repeats |

**Cast lifecycle patterns** (how the roster evolves — the thing that turns a feed into a
*following*):

- **Fixed ensemble** (Horoscope's 12 signs, Feng Shui's 12 animals): recurring cast = retention.
- **Anchor + rotating guests** (History's narrator, Petty Court's judge): brand continuity, infinite guests.
- **Serial progression** (Sun Tzu protagonist levels up): same cast, evolving arcs.
- **Audience-mutated** (Branching, Versus): the crowd kills/keeps characters — peak interactivity.
- **Reality-tracking** (Markets): cast mirrors the real world's winners/losers.
- **Seasonal swap** (Reality Olympus seasons, themed decks/weeks): scheduled format refresh, no code change.

**Style/animation rule of thumb.** Contemplative/reading formats (Horoscope, Tarot,
Feng Shui, History docs) → **Ken Burns** + low soundtrack. Confrontation/action formats
(Sun Tzu duels, Markets battles, Versus clashes, Branching action) → **Kling** animation.
Match aspect to platform: 9:16 default; add 16:9 for anything education/YouTube-leaning
(History); 1:1 for screenshot-heavy formats (Feng Shui, Markets).

---

## How to actually build one (mechanics)

The engine is the show-agnostic **`marketing/showrunner/`**; a new show is just a
**directory of config + sourcing** beside `BreakingBricksNews/`. The uploader
never changes. The [`showrunner/README.md`](../../showrunner/README.md) is the
canonical how-to; in short:

1. **Create the campaign** in the app: pick the art **style**, **aspect ratio**, and
   set up the **cast** (recurring characters with their images/voices and per-character
   subtitle font/color — see the cast-styling notes in the API; custom rosters live in
   `movie_custom_cast`). Note the `campaignId`.
2. **Make the show dir + `show.env`** — `marketing/<Show>/show.env` carries
   `CAMPAIGN_ID`, `SOUNDTRACK_AUDIO_PATH`, `VOLUME`, `CAST_ALIASES`
   (`"Full Name=Alias,…"`), `STORY_GLOB`/`STORY_SUFFIX`, `CADENCE`, `ENGINE`,
   `PREPARE_KIND`. The cast map lives here as **data** — no engine code changes.
3. **Add the sourcing** in the show dir (this is the only per-show "code"), picking
   an archetype. `showrunner/prepare.sh <showDir>` dispatches to it:
   - *Computed* → `compute.py` (deterministic; **see the working
     [`../../Horoscopes/compute.py`](../../Horoscopes/compute.py)**). No model needed.
   - *WebFetch / Extracted* → `prompt.md` with `{{OUTPUT_FILE}}`/`{{TIMESTAMP}}`
     placeholders, driven by `claude -p` (as BBN's
     [`../prompt.md`](../prompt.md) does).
   - *Randomized* → a **date-seeded** generator so runs are reproducible; log the seed.
   For lifecycle/serial shows, the sourcing step should **read prior episodes' state**
   (the campaign's movies, a local cursor file, or the last post's engagement) first.
4. **Run it** with the existing engine — any of the three ports, same flags:
   ```bash
   ./marketing/showrunner/prepare.sh             marketing/<Show>
   python3 ./marketing/showrunner/upload_to_yakyak.py --show marketing/<Show> --post --yes
   ```
   (`--volume`/`--soundtrack` override `show.env` if you need a per-run tweak.)
5. **Schedule it.** Set `CADENCE`/`ENGINE`/`ENABLED` in `show.env` and the GitHub
   Actions matrix picks it up automatically (render-only by default, `post` opt-in).
   See [`yakyak_upload_usage.md`](yakyak_upload_usage.md) and
   [`showrunner/README.md`](../../showrunner/README.md#ci-github-actions).
   Branching/Versus jobs must read results *before* generating, so have the
   sourcing step consult engagement first.

**One IP caveat for the source-heavy shows:** stick to **public-domain or licensed**
texts (Art of War, Book of Five Rings, Shakespeare, classical myth, pre-1929 works) and
**paraphrase/transform** scraped content (Reddit) rather than reproducing it verbatim —
keeps you clear of copyright and platform rules while staying fully viral.

---

## Related

- [`../../showrunner/README.md`](../../showrunner/README.md) — the engine + how to add a show.
- [`yakyak_upload_usage.md`](yakyak_upload_usage.md) — uploader flags, cron, Docker, CI.
- [`how_it_works.md`](how_it_works.md) — end-to-end pipeline overview.
- `marketing/showrunner/story-format.js` — the story-markdown → payload contract, in code.
