# MarketMayhem

> **Market Mayhem — Crypto & Markets Daily**: a daily dark-comedy newscast where personified market characters — Bitcoin, Ethereum, Doge, The Fed, Gold — react to the day's **real** price action, anchored by the manic Max Mayhem.

One of the eight example **shows** in the YakYak cookbook. Like every show it is just a `show.env` plus a story source, wired to the shared engine in [`../showrunner/`](../showrunner/) and run on auto-pilot: **source → render → (optionally) post**. See [`../README.md`](../README.md) for the gallery and the sourcing taxonomy.

## What this show is

A vertical (9:16) daily short. Each episode is eight scenes of anime/manga-styled market satire: a recurring cast of six characters reacting to the day's genuine crypto prices and market sentiment. Real price moves drive the plot; the comedy comes from each character's voice and how they react to the numbers. The cold open and the sign-off are always the anchor, **Max Mayhem**; scenes 2–7 are the five personified assets reacting, with the day's biggest mover getting the strongest beat.

Within the cookbook's sourcing taxonomy this is the **Prompt / WebFetch + model** example: `PREPARE_KIND="prompt"`, `REQUIRES_MODEL="true"`, engine `py`, cadence `daily`.

## What it demonstrates

- **Live external-data sourcing via WebFetch.** Each episode's story is built from data fetched *that day* from public, no-key JSON endpoints — Binance's 24h ticker for BTC/ETH/DOGE and the alternative.me Crypto Fear & Greed Index — not from a baked corpus or a deterministic compute step.
- **Personified-cast dramatization.** Raw numbers (percent changes, last price, a 0–100 sentiment value) are turned into a story by a fixed cast of characters with consistent personalities, so the same machinery produces a fresh-but-familiar episode every day. A green day and a red day are required to *feel* different.
- **Distinct voice per character.** Every cast member has its own TTS voice and its own subtitle accent color, so the six characters read as six characters on screen and in audio.

## How it works

### Story sourcing

`PREPARE_KIND="prompt"` means `prepare.sh` runs [`prompt.md`](prompt.md) through `claude -p` (which has the **WebFetch** and **Write** tools). The prompt instructs the model to, in order:

1. **Fetch the data** — one WebFetch call per URL, all free server-rendered JSON needing no API key:
   - `https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT` (Bitcoin 24h)
   - `https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT` (Ethereum 24h)
   - `https://api.binance.com/api/v3/ticker/24hr?symbol=DOGEUSDT` (Doge 24h)
   - `https://api.alternative.me/fng/` (Crypto Fear & Greed Index)

   From each Binance response it extracts `lastPrice`, `priceChangePercent` (24h % change), and the 24h high/low. From Fear & Greed it extracts the latest `value` (0–100) and its `value_classification` (e.g. "Greed", "Fear"). If Binance is geo-blocked (**HTTP 451**, common on US servers) it falls back to a single CoinGecko endpoint — `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,dogecoin&vs_currencies=usd&include_24hr_change=true` — for all three prices plus 24h change. If a fetch still fails it notes that and proceeds with whatever it got; it must **never invent numbers**. Gold and The Fed have no live feed: Gold is dramatized qualitatively against the risk-on/risk-off mood, and The Fed plays the macro "interest-rate / disapproving parent." (The two committed sample stories in `stories/` show both paths — one cites the Binance 24h ticker, the other the CoinGecko fallback.)

2. **Compute the read** (in reasoning, no tools) — the day's biggest **gainer** and biggest **loser** among BTC/ETH/DOGE, the overall **mood** (risk-on green day vs risk-off red day), and the Fear & Greed classification as the "emotional weather" of the episode. *This computed read is the plot.*

3. **Write the story** — exactly 8 scenes. Scene 1 is Max Mayhem cold-opening with the day's headline mood; scenes 2–7 are the five assets reacting (the biggest mover gets the spotlight, and may take a second scene instead of a quiet one being repeated); scene 8 is Max Mayhem signing off. Only the six cast names may speak; each scene names exactly one leading character from the cast. Each scene carries ~200 words of director's-brief prose (leaning on green/red color and candlestick/ticker imagery) and exactly one spoken line of 8–12 words that must not end in a period. Tone is dark comedy / market satire — no financial advice, no buy/sell calls, no slurs, punch up not down.

4. **Save** the markdown to the engine-provided absolute path (`{{OUTPUT_FILE}}`), with a fixed header block listing the generation UTC timestamp, the sources used, and a "Headlines we drew from" bullet list of the real data points. The model replies with only the file path.

The story-format header tells `prepare.sh` to write files matching `STORY_GLOB="*_market_mayhem.md"` (suffix `_market_mayhem.md`), which the engine then renders.

### Cast & style

`CAST_ALIASES` maps the bare leading-character names the prompt emits to the campaign's cast: `Max Mayhem`, `The Fed`, `Bitcoin`, `Ethereum`, `Doge`, `Gold`. (Max Mayhem and The Fed are listed first so their multi-word names win the substring match unambiguously.)

The campaign config (`campaign.import.json`) is the source of truth and pins the look and the per-character treatment. The campaign uses the **Anime / Manga** style, `aspectRatio` **9:16**, renders with **Kling**, with the color language "green means up, red means down." Each character has a fixed visual description, a **distinct TTS voice**, and its own **Keania One** subtitle accent color:

| Character | Role | Voice | Subtitle color | Personality |
|-----------|------|-------|----------------|-------------|
| Max Mayhem | anchor (Guru) | Patrick | `#FF3B30` (red) | Manic late-night anchor; opens scene 1, closes scene 8 |
| Bitcoin | Protagonist | Roger | `#F7931A` (orange) | Smug veteran who's seen every crash |
| Ethereum | Protagonist | Liam | `#627EEA` (blue) | Earnest, over-explaining younger sibling |
| Doge | Protagonist | Jeremy | `#F2C94C` (yellow) | Chaos-gremlin Shiba Inu memecoin |
| The Fed | Antagonist | Paul | `#2E7D5B` (green) | Stern, deadpan disapproving parent |
| Gold | Antagonist | Michael | `#D4AF37` (gold) | Slow, smug "back in my day" boomer bullion |

The campaign renders with **Kling** (`animationType` is `kling`) — AI video generation for the finished look. While refining the channel you can switch `animationType` to **Ken Burns** — a pan/zoom over the still — which renders **faster and cheaper**, then switch back to Kling for the finished look. The import carries the cast roster, voices, subtitle colors, and 9:16 config but **no rendered assets** — the one-time setup generates the six cast portraits, composes the soundtrack, renders a trailer, and bootstraps season 1.

### Render & post

- **Engine:** `ENGINE="py"` (the Python port; all three ports produce identical results).
- **Soundtrack:** one AI-composed track, reused by every episode, pinned at `SOUNDTRACK_AUDIO_PATH` (`prd/ugc/.../1386f826-….mp3`). It is composed once on the template from `MUSIC_PROMPT` — a "tense electronic instrumental: pulsing synth arpeggios, driving bassline, ticking-clock percussion … financial-thriller energy" — then written back. `VOLUME="45"`.
- **Cadence:** `CADENCE="daily"` (intended to run at market close — the flagship daily-cron case).
- **Flags:** `ENABLED="false"` (the show is off until you set it true after a verified local setup and first render) and `POST="false"` (render-only on scheduled runs; set true to irreversibly publish to social). `MIN_TOKEN_BALANCE="2000"` guards renders against a low account balance.

## Files in this directory

| File | Purpose |
|------|---------|
| [`show.env`](show.env) | The show's entire configuration (campaign id, cast aliases, sourcing kind, cadence, render/post flags). |
| [`prompt.md`](prompt.md) | The `claude -p` prompt that fetches the day's market data and writes one 8-scene story file. |
| [`campaign.import.json`](campaign.import.json) | The campaign template and source of truth — cast roster, voices, Keania One subtitle colors, Anime/Manga style, 9:16, Kling animation. Imported once by the setup step; carries no rendered assets. |
| [`stories/`](stories/) | Output directory for generated `*_market_mayhem.md` episode stories (two sample episodes are committed; `.gitkeep` keeps it tracked). |
| `.gitattributes` | Stores this show's text source inline (diffable) rather than as Git LFS pointers; future binary brand assets stay in LFS. |

## Configuration

Selected keys from [`show.env`](show.env) (no secrets — the PAT and API key come from the environment):

| Key | Value | Meaning |
|-----|-------|---------|
| `CAMPAIGN_ID` | `42ebdc7c-3d88-496b-9bce-bf6e4e888256` | The YakYak campaign this show renders into. |
| `SOUNDTRACK_AUDIO_PATH` | `prd/ugc/…/1386f826-….mp3` | The composed soundtrack reused by every episode. |
| `MUSIC_PROMPT` | tense electronic financial-thriller instrumental | Mood for the one-time soundtrack compose. |
| `VOLUME` | `45` | Soundtrack volume. |
| `MIN_TOKEN_BALANCE` | `2000` | Skip rendering below this account token balance. |
| `STORY_GLOB` | `*_market_mayhem.md` | Which prepared story files the engine renders. |
| `STORY_SUFFIX` | `_market_mayhem.md` | Suffix `prepare.sh` writes (`<UTC-ts><suffix>`). |
| `CAST_ALIASES` | `Max Mayhem=…,The Fed=…,Bitcoin=…,Ethereum=…,Doge=…,Gold=…` | Maps emitted leading-character names to cast members. |
| `PREPARE_KIND` | `prompt` | Source each episode via `prompt.md` + `claude -p` (WebFetch). |
| `REQUIRES_MODEL` | `true` | CI hint: prepare needs `ANTHROPIC_API_KEY` and the prepare image. |
| `CADENCE` | `daily` | Scheduled to run daily. |
| `ENGINE` | `py` | Use the Python port of the engine. |
| `ENABLED` | `false` | Off until you flip it true after a verified setup. |
| `POST` | `false` | Render-only on scheduled runs (true = publish to social, irreversible). |

## Run it

From the repo root, using the `py` ports of the engine. **One-time campaign setup** (only if `CAMPAIGN_ID` is empty — imports `campaign.import.json`, generates the six cast portraits, composes the soundtrack, renders a trailer, bootstraps season 1, and fills the ids back into `show.env`):

```sh
YAKYAK_PAT=yy_live_... ./show/showrunner/setup_show.sh show/MarketMayhem
```

**Source the day's story** (fetches live data via `claude -p`; needs `ANTHROPIC_API_KEY`):

```sh
./show/showrunner/prepare.sh show/MarketMayhem
```

**Render / upload the prepared episode** (add `--post --yes` to publish):

```sh
./show/showrunner/upload_to_yakyak.py --show show/MarketMayhem
```

## Notes & gotchas

- **Live-data dependency.** Because the story is built from real-time endpoints, sourcing can fail or shift with network and API availability. Binance is frequently geo-blocked from US servers (**HTTP 451**) — the prompt falls back to CoinGecko for prices, but the Fear & Greed call has no fallback. The prompt is instructed to proceed with whatever it fetched and **never invent numbers**, so a partial-data day still produces an episode, just with fewer cited data points.
- **`REQUIRES_MODEL="true"`.** The prepare step runs `claude -p`, so it needs a Claude credential (`ANTHROPIC_API_KEY`) and, in CI, the prepare image that bundles the `claude` CLI. Compute-kind shows do not need this; this one does.
- **Disabled by default.** `ENABLED="false"` and `POST="false"` — the show will not auto-run or auto-publish until you flip both after a verified local setup and first render.
- **Anime/manga + named entities.** The cast are original personifications (not real logos/people), which keeps the show clear of the content-moderation pitfalls described for `OnThisDay` in [`../README.md`](../README.md). Still confirm the day's render before enabling auto-post.

## Reference

- Show gallery & sourcing taxonomy: [`../README.md`](../README.md)
- Engine config & key reference: [`../showrunner/README.md`](../showrunner/README.md)
- Pipeline / campaign → movie → scene model & debugging: [`../../docs/`](../../docs/)
- Product: https://yakyak.ai/
- API docs: https://api.yakyak.ai/api/docs
