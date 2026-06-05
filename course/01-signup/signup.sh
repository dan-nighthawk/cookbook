#!/usr/bin/env bash
# Lesson 1 (bash/curl): sign up, confirm email, then mint a non-expiring Personal
# Access Token (PAT) and save it to .env. If YAKYAK_PASSWORD is blank, a strong
# password is generated and saved to .env (use it to sign into the web app too).
# Later lessons use the PAT — no re-auth.
# Run:  bash 01-signup/signup.sh     (from the course/ folder)
set -euo pipefail

ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
[ -f "$ENV_FILE" ] || { echo "Create course/.env from .env.example first."; exit 1; }
set -a; . "$ENV_FILE"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_EMAIL:?}"
field() { python3 -c "import sys,json;v=json.load(sys.stdin).get('$1');print('' if v is None else v)"; }

# Generate a strong password: length 14, includes A-Z, a-z, 0-9, and a special
# from !@#$%^&* (at least one digit and one special).
gen_password() {
  python3 - <<'PY'
import secrets, string
pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, "!@#$%^&*"]
allc = "".join(pools)
chars = [secrets.choice(p) for p in pools]
chars += [secrets.choice(allc) for _ in range(14 - len(chars))]
secrets.SystemRandom().shuffle(chars)
print("".join(chars))
PY
}

# Set KEY=value in .env. Pass a 3rd arg to single-quote the value (for the
# password, which contains shell-special characters).
set_env() {
  python3 - "$ENV_FILE" "$1" "$2" "${3:-}" <<'PY'
import re, sys
path, key, val, quote = sys.argv[1:5]
v = "'" + val + "'" if quote else val
txt = open(path).read()
pat = re.compile(rf'^{key}=.*$', re.M)
line = f"{key}={v}"
txt = pat.sub(lambda m: line, txt) if pat.search(txt) else txt + ('' if txt.endswith('\n') else '\n') + line + '\n'
open(path, 'w').write(txt)
PY
}

if [ -z "${YAKYAK_PASSWORD:-}" ]; then
  YAKYAK_PASSWORD="$(gen_password)"
  set_env YAKYAK_PASSWORD "$YAKYAK_PASSWORD" quote
  echo "🔐 Generated a password and saved it to course/.env (use it to sign into the web app too)."
fi

echo "Creating account for $YAKYAK_EMAIL …"
curl -s -X POST "$YAKYAK_API_BASE/users/create-by-email" -H "Content-Type: application/json" \
  -d "{\"email\":\"$YAKYAK_EMAIL\",\"password\":\"$YAKYAK_PASSWORD\"}" >/dev/null || true

# Confirmation is a link click. login-by-email only returns a token once confirmed,
# so poll it until it succeeds.
echo "👉 Open your inbox and click the confirmation link for $YAKYAK_EMAIL."
SESSION=""; USER_ID=""
for _ in $(seq 1 60); do
  RESP=$(curl -s -X POST "$YAKYAK_API_BASE/users/login-by-email" -H "Content-Type: application/json" \
    -d "{\"email\":\"$YAKYAK_EMAIL\",\"password\":\"$YAKYAK_PASSWORD\"}")
  SESSION=$(printf '%s' "$RESP" | field token)
  if [ -n "$SESSION" ]; then USER_ID=$(printf '%s' "$RESP" | field userId); break; fi
  echo "  waiting for confirmation… (click the link; retrying in 10s)"
  sleep 10
done
[ -n "$SESSION" ] || { echo "Timed out waiting for email confirmation."; exit 1; }

# Mint a non-expiring Personal Access Token using the (short-lived) session token.
echo "Creating a Personal Access Token…"
PAT=$(curl -s -X POST "$YAKYAK_API_BASE/access-tokens" -H "Authorization: Bearer $SESSION" \
  -H "Content-Type: application/json" \
  -d '{"name":"YakYak course","scopes":["video_creation","social_publishing","account_management"]}' | field token)
[ -n "$PAT" ] || { echo "Failed to create access token."; exit 1; }

set_env YAKYAK_TOKEN "$PAT"
set_env YAKYAK_USER_ID "$USER_ID"
echo "✅ PAT saved to course/.env (it doesn't expire — no re-auth in later lessons)."
COUNT=$(curl -s "$YAKYAK_API_BASE/data/style" -H "Authorization: Bearer $PAT" | field count)
echo "Smoke test with the PAT: $COUNT styles available — you're ready for Lesson 2."
