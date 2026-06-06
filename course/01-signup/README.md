# Lesson 1 — Sign up & get a Personal Access Token

Create an account, confirm your email, and mint a **Personal Access Token (PAT)** —
a **non-expiring** key saved to `course/.env`. Every later lesson uses the PAT, so
there's no more signing in.

If you leave `YAKYAK_PASSWORD` blank, the scripts **generate a strong password** for
you (14 characters with upper- and lower-case letters, a digit, and a special) and
save it to `course/.env` — you can use that same password to **sign into the YakYak
web app**.

Every step in this course can be done three ways — in the **YakYak web app (GUI)**,
with **plain REST** (`curl`), or with the **SDK clients (JavaScript / Python)**. The
screencast below shows the GUI; the runnable scripts that follow do exactly the same
thing via REST and the SDK. Pick whichever you prefer — they're interchangeable.

> Why a PAT and not the login JWT? The token from `login-by-email` is a short-lived
> session token. A PAT (`yy_live_…`) doesn't expire, so the course only authenticates
> once.

## Watch it

<video src="../assets/screencast/01-signup.mp4" controls width="100%"></video>

▶ If the video doesn't play inline, [open the screen recording](../assets/screencast/01-signup.mp4) —
it walks through signing up and creating a PAT in the web app.

## What the script does

1. If `YAKYAK_PASSWORD` is blank, **generates a strong password** and saves it to
   `course/.env` (it also works for web-app sign-in).
2. `POST /users/create-by-email` — creates the account and emails a **confirmation link**.
3. Polls `POST /users/login-by-email` every 10 s — it only returns a session token
   **after** you click the link, so this doubles as "wait for confirmation".
4. `POST /access-tokens` with that session token →
   `{ name, scopes: ["video_creation","social_publishing","account_management"] }`
   returns your **PAT**.
5. Writes `YAKYAK_TOKEN` (the PAT) and `YAKYAK_USER_ID` to `course/.env`.
6. Smoke-tests the PAT by listing styles.

## Run it

From `course/`, create your `.env` first:

```bash
cp .env.example .env
# edit .env: set YAKYAK_EMAIL. Leave YAKYAK_PASSWORD blank to auto-generate one
# (or set your own). YAKYAK_API_BASE defaults to beta.
```

Then pick a language:

```bash
bash 01-signup/signup.sh        # bash + curl
npm install && node 01-signup/signup.js   # JavaScript (yakyak-sdk)
pip install -r requirements.txt && python 01-signup/signup.py   # Python (yakyak-sdk)
```

Each script pauses on "waiting for confirmation…" — open the email, click the link,
and it continues, mints the PAT, and writes it to `.env`.

## Managing tokens

```bash
# list your PATs (id, name, scopes, tokenHint)
curl -s "$YAKYAK_API_BASE/access-tokens" -H "Authorization: Bearer $YAKYAK_TOKEN"
# revoke one
curl -s -X DELETE "$YAKYAK_API_BASE/access-tokens/<id>" -H "Authorization: Bearer $YAKYAK_TOKEN"
```

## Notes

- **Scopes**: `video_creation` (campaigns/episodes), `social_publishing` (posting),
  `account_management`. The course requests all three.
- **Base URL is overridable** — `.env`'s `YAKYAK_API_BASE` and the SDK's
  `baseUrl`/`host` point at beta; swap to `https://api.yakyak.ai` for production.
- The PAT is shown **once** at creation — that's why we save it to `.env` immediately.
- JS/Python need `yakyak-sdk` ≥ 0.0.7 (see the course [README](../README.md#2-prerequisite-sdk--007)).

---

**Next:** [Lesson 2 — Hello, world: fork Fruit Island & render](../02-hello-world/README.md) ⭐
