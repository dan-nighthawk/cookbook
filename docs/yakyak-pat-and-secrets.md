# YakYak PAT & GitHub Actions secrets

The showrunner authenticates to the YakYak API with a **personal access token (PAT)**
— a string shaped `yy_live_…`. In CI that PAT lives as an **encrypted repository
secret** named `YAKYAK_PAT`, which the workflows read at runtime. This doc covers
both halves: minting the token, and adding it (plus the optional secrets) to your
fork.

---

## Part 1 — Mint a YakYak PAT

1. Sign in at [yakyak.ai](https://yakyak.ai/) and open **`/profile`**.
2. Under **Personal Access Tokens**, click **+ New token**.
3. Name it (e.g. `showrunner-ci`) and choose scopes:
   - **`video_creation`** — required (generate, upload, render).
   - **`social_publishing`** — add **only** if you'll auto-post episodes to social
     (the `POST` flag / `post` dispatch input). Omit it for render-only.
4. Create it, then **copy the `yy_live_…` value immediately** — it's shown once and
   never again. If you lose it, revoke and mint a new one.

> **Top up the balance first.** Producing episodes costs tokens — the one-time
> campaign setup generates cast portraits, composes a soundtrack, and renders a
> trailer; each episode then renders too. The free signup grant won't cover a full
> setup. The scripts **abort** when the balance is below `MIN_TOKEN_BALANCE`
> (default 2000). (CI's fork-heal path avoids the paid setup by *forking* an existing
> campaign instead — see [`forking.md`](./forking.md) — but rendering each episode
> still costs tokens.)

The token encodes your `userId`; the showrunner decodes it from the PAT itself, so
there's nothing else to configure. The API base defaults to `https://api.yakyak.ai`.

---

## Part 2 — Add the PAT as a repository secret

GitHub **encrypted secrets** are write-only: you paste the value once, Actions can
read it at runtime, and no one (including you) can read it back through the UI.

1. In your fork, go to **Settings → Secrets and variables → Actions**.
2. On the **Secrets** tab, click **New repository secret**.
3. **Name:** `YAKYAK_PAT` (exact — the workflows reference `secrets.YAKYAK_PAT`).
   **Secret:** paste your `yy_live_…` token.
4. **Add secret.**

That single secret is enough to **render**. Official reference: GitHub's
[**Using secrets in GitHub Actions**](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions).

---

## Optional secrets & variables

Add these only if the matching condition applies:

| Name | Kind | When you need it |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | secret | A show whose story is written by a model (`REQUIRES_MODEL="true"`, the *prompt/WebFetch* shows). Used in the **Prepare story** step. Metered against API credit. |
| `CLAUDE_CODE_OAUTH_TOKEN` | secret | Alternative to `ANTHROPIC_API_KEY` for model shows — a Claude **subscription** token, *not* metered against API credit. If both are set, CI prefers this one. |
| `DOCKER_HUB_PAT` | secret | Only to dodge anonymous Docker Hub pull rate limits (or for private images). The engine images pull anonymously without it — skip unless you hit pull errors. |
| `SHOWRUNNER_TAG` | **variable** | Pin runs to a known-good engine image tag for reproducibility/rollback. Defaults to `latest` when unset. Set under the **Variables** tab, not Secrets. |

> **Render-only needs just `YAKYAK_PAT`** — and only for *computed* shows (e.g.
> Horoscopes, LuckyDay), which need no model key at all. A *prompt* show
> additionally needs `ANTHROPIC_API_KEY` **or** `CLAUDE_CODE_OAUTH_TOKEN`. Posting
> additionally needs the PAT minted with the `social_publishing` scope.

---

## Rotating or revoking

- **Rotate the PAT:** mint a new one at `/profile`, update the `YAKYAK_PAT` secret
  (same name overwrites the value), then revoke the old token.
- **Revoke immediately** if a token leaks (e.g. printed to a log). Secrets are masked
  in Actions logs, but treat any exposure as compromised.

---

## See also

- [`github-forking.md`](./github-forking.md) — fork the repo and enable Actions
  (do this first).
- [`scheduling.md`](./scheduling.md) — the cron schedule and the `ENABLED` / `POST`
  flags that decide *when* a show runs and *whether* it posts.
- [`../show/README.md`](../show/README.md#how-to-run-a-show) — the full "How to run a
  show" walkthrough.
- [`../show/showrunner/FORKING.md`](../show/showrunner/FORKING.md) — minting a PAT for
  the *local* (no-CI) path, and the one-time campaign setup.
