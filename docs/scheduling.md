# Scheduling shows: cron, `ENABLED`, and `POST`

Once your fork is set up (repo forked + Actions enabled + `YAKYAK_PAT` added), the
**Render Shows** workflow (`.github/workflows/run-shows.yml`) can run your channel on
auto-pilot. Three knobs decide *when* it runs and *whether* it publishes:

- the workflow's **cron schedule** + each show's **`CADENCE`** — *when* a show is due;
- each show's **`ENABLED`** flag — *whether* scheduled runs touch it at all;
- each show's **`POST`** flag (or the `post` dispatch input) — *whether* a run
  publishes to social, or only renders.

---

## The cron schedule

`run-shows.yml` carries a single daily trigger:

```yaml
on:
  schedule:
    - cron: '50 6 * * *'      # 06:50 UTC daily
```

Each day the **`plan`** job scans every `show/*/show.env` (`plan_due_shows.sh`) and
builds the matrix of shows that are **due today** — so one daily tick fans out to the
right subset rather than each show owning its own cron line.

A show declares its own rhythm with **`CADENCE`** in `show.env`; the planner maps it
to the current UTC day-of-week:

| `CADENCE` | Runs on | Notes |
| --- | --- | --- |
| `daily` (default) | every day | |
| `weekly` | **Sundays** (DOW 7) | |
| `mwf` | **Mon / Wed / Fri** | 3× per week |
| *(anything else)* | every day | unknown values fall back to daily |

### Changing when it runs

Edit the `cron:` line and commit it to your default branch. Cron is **5-field, UTC
only**, minimum 5-minute granularity:

```
┌ minute (0–59)
│ ┌ hour (0–23, UTC)
│ │ ┌ day-of-month (1–31)
│ │ │ ┌ month (1–12)
│ │ │ │ ┌ day-of-week (0–6, Sun=0)
│ │ │ │ │
50 6 * * *      # 06:50 UTC every day
```

GitHub cron caveats worth knowing:

- **UTC only** — there's no timezone option; convert your local time yourself.
- **No exact guarantees** — scheduled runs can be **delayed during peak load** (often
  several minutes; sometimes dropped entirely on the hour boundary). Picking a minute
  *off* the hour, like `50`, dodges the worst of it.
- **Forks start paused** — the schedule only fires after you've **enabled Actions**
  on the fork, and GitHub **auto-disables scheduled workflows after 60 days of no
  repo activity** (it emails you to re-enable). See
  [`github-forking.md`](./github-forking.md#2-enable-actions-on-the-fork).

Full reference: GitHub's
[**Events that trigger workflows → `schedule`**](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
and the [POSIX cron syntax](https://crontab.guru/) it accepts.

> You can leave the schedule alone and always trigger runs by hand — see **Running on
> demand (dispatch)** in [`../show/README.md`](../show/README.md#3-run-it-dispatch-or-cron).

---

## The `ENABLED` flag — opt a show in or out of cron

In each `show/<Show>/show.env`:

```bash
ENABLED="true"    # default; "false" = skip this show in scheduled runs
```

- `ENABLED="false"` removes the show from the **scheduled** matrix entirely — the
  cron tick ignores it no matter what its `CADENCE` says.
- It does **not** block a manual run: the `show` dispatch input **forces** that one
  show regardless of `ENABLED` or `CADENCE`. Use that to test a disabled show
  on demand.

This is how you stage a new show — commit it `ENABLED="false"`, exercise it by hand
until it's solid, then flip it to `true`.

---

## The `POST` flag — render-only vs. publish

**Every run is render-only unless you explicitly opt into posting.** Posting to
social is **irreversible**, so it's gated two independent ways — either turns posting
on for a run:

```bash
# in show.env — publish on EVERY scheduled run of this show
POST="true"      # default "false" = render only
```

…**or** the **`post` dispatch input** when you trigger a run by hand (a per-run
override that posts whichever shows that run touches).

Internally the engine still requires a `--yes` confirmation to post unattended, and
posting needs the PAT minted with the **`social_publishing`** scope (see
[`yakyak-pat-and-secrets.md`](./yakyak-pat-and-secrets.md)). If neither the flag nor
the input is set, the run renders and stops — nothing is published.

> Posting an **already-rendered** episode (no re-render) is a separate manual
> workflow, **Post Episode** (`post-show.yml`) — dispatch-only, since it publishes.

---

## Quick reference

| I want to… | Do this |
| --- | --- |
| Run every day at a different UTC time | Edit the `cron:` line in `run-shows.yml` |
| Make a show weekly / Mon-Wed-Fri | Set `CADENCE="weekly"` / `"mwf"` in its `show.env` |
| Stop a show from running on cron | Set `ENABLED="false"` in its `show.env` |
| Test a disabled show now | Dispatch with the `show` input = its basename |
| Publish on every scheduled run | Set `POST="true"` (+ `social_publishing` PAT scope) |
| Publish just this one manual run | Dispatch with the `post` input checked |
| Render now, never publish | Leave `POST="false"` and the `post` input unchecked |

---

## See also

- [`../show/README.md`](../show/README.md#how-to-run-a-show) — the full "How to run a
  show" walkthrough (fork → secret → run → fork-heal → import).
- [`github-forking.md`](./github-forking.md) — forking the repo and the
  forks-and-cron caveats.
- [`yakyak-pat-and-secrets.md`](./yakyak-pat-and-secrets.md) — the secrets a run reads.
- [`../show/showrunner/README.md`](../show/showrunner/README.md) — the full `show.env`
  key reference and the engine's non-interactive gates.
