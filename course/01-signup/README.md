# Lesson 1 — Sign up & get your token

Create an account, confirm your email, and save a Bearer token to `course/.env` so
every later lesson can authenticate.

## What the script does

1. `POST /users/create-by-email` — creates the account (a no-op if it already exists).
2. Tells you to **click the confirmation link** emailed to you, then **polls
   `login-by-email` every 10 seconds** until the account is confirmed.
3. Writes `YAKYAK_TOKEN` and `YAKYAK_USER_ID` into `course/.env`.
4. Smoke-tests the token by listing styles.

> Most write calls need both the token **and** your `userId`, so we save both.

## Run it

First, from the `course/` folder, create your `.env`:

```bash
cp .env.example .env
# edit .env: set YAKYAK_EMAIL and YAKYAK_PASSWORD (YAKYAK_API_BASE defaults to beta)
```

Then pick a language:

```bash
# bash + curl
bash 01-signup/signup.sh
```

```bash
# JavaScript (uses the yakyak-sdk client)
npm install
node 01-signup/signup.js
```

```bash
# Python (uses the yakyak-sdk client)
pip install -r requirements.txt
python 01-signup/signup.py
```

Each script pauses on "waiting for confirmation…" — open the email, click the link,
and it continues automatically and writes your token.

## Notes

- **Base URL is overridable.** `.env`'s `YAKYAK_API_BASE` (and the SDK's
  `baseUrl`/`host`) point at `https://api.beta.yakyak.ai` for the tutorial; swap to
  `https://api.yakyak.ai` for production.
- **Already confirmed?** The login poll succeeds on the first try and you're done.
- **SDK version.** The JS/Python scripts need `yakyak-sdk` ≥ 0.0.5 (see the course
  [README](../README.md#prerequisite-sdk-005)).

---

**Next:** [Lesson 2 — Hello, world: fork Fruit Island & render](../02-hello-world/README.md) ⭐
