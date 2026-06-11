# Forking this repo on GitHub

To run the showrunner on auto-pilot you run it **as a GitHub Actions workflow in your
own copy of this repository**. A *fork* is GitHub's word for that copy: your own
repo, seeded with everything here — the shows, the `showrunner/` engine, and the
`.github/workflows/` that drive them — but owned by your account, so it can hold your
secrets and run on your Actions minutes.

> This is **GitHub-repo forking** (copy the repository). Don't confuse it with
> **YakYak campaign forking** (copy a rendered campaign so you don't pay to
> re-render) — that's a different mechanism entirely, covered in
> [`forking.md`](./forking.md). The CI uses *both*: you fork the repo here, and the
> running show forks the *campaign* so it's owned by your PAT (see the fork-heal
> decision tree in [`../show/README.md`](../show/README.md#4-the-fork-heal-step-owned-or-fork)).

---

## 1. Create the fork

1. Open this repository on GitHub and click **Fork** (top-right).
2. Pick your account as the **owner**. Leave **"Copy the `main` branch only"**
   checked — that's all the workflows need.
3. Click **Create fork**. After a few seconds you land on
   `https://github.com/<you>/<repo>`, your own copy.

Full official walkthrough: GitHub's
[**Fork a repository**](https://docs.github.com/en/get-started/quickstart/fork-a-repo)
guide.

> **Private vs. public.** A fork of a public repo is public by default. If you want
> your channel's stories and committed campaign ids kept private, create the fork and
> then set it private under **Settings → General → Danger Zone → Change visibility**
> (or import the repo as a private mirror instead of forking). Actions minutes are
> free for public repos and metered for private ones.

---

## 2. Enable Actions on the fork

GitHub **disables workflows on new forks by default** — a safety measure so a fork
can't run someone else's automation unprompted. You must turn them on once:

1. Open the **Actions** tab of your fork.
2. Click **"I understand my workflows, go ahead and enable them."**

Until you do this, neither the manual **Run workflow** button nor the daily cron will
appear or fire.

> **Scheduled (cron) runs need extra care on forks:**
> - The `schedule:` trigger only starts firing **after** you've enabled Actions
>   (above) **and** the workflow file exists on your default branch.
> - GitHub **automatically disables scheduled workflows after 60 days of repository
>   inactivity** (no pushes). A daily render keeps it alive; if your channel goes
>   quiet, GitHub emails you to re-enable it.
>
> See [`scheduling.md`](./scheduling.md) for the cron details and the per-show
> `ENABLED` / `POST` flags.

---

## 3. Add your secrets, then run

A fork starts with **no secrets** — yours don't carry over and neither do the
upstream repo's. Before the first run, add at least your `YAKYAK_PAT`:
see [`yakyak-pat-and-secrets.md`](./yakyak-pat-and-secrets.md).

Then trigger a show — manually via **Run workflow**, or wait for the daily cron.
Both paths, and the optional posting step, are described in the **How to run a show**
section of [`../show/README.md`](../show/README.md#how-to-run-a-show).

---

## Keeping your fork up to date (optional)

Upstream keeps adding shows and engine fixes. To pull them in, open your fork on
GitHub and click **Sync fork → Update branch**, or from a local clone:

```bash
git remote add upstream https://github.com/<upstream-owner>/<repo>.git
git fetch upstream
git merge upstream/main          # or: git rebase upstream/main
git push origin main
```

Your own additions live in `show/<YourShow>/` and in each show's committed
`CAMPAIGN_ID`, so syncing rarely conflicts. If two shows touched the same
`show.env`, resolve it the normal way and push.

---

## See also

- [`yakyak-pat-and-secrets.md`](./yakyak-pat-and-secrets.md) — mint a YakYak PAT and
  add it (plus optional model/Docker secrets) to your fork.
- [`scheduling.md`](./scheduling.md) — the cron schedule and the `ENABLED` / `POST`
  flags.
- [`../show/README.md`](../show/README.md#how-to-run-a-show) — the end-to-end "How to
  run a show" walkthrough.
- [`forking.md`](./forking.md) — the *other* fork (YakYak campaign forking) the CI
  relies on so each show is owned by your PAT.
