#!/usr/bin/env bash
# Lesson 1 (bash/curl): sign up, confirm email, then mint a non-expiring Personal
# Access Token (PAT) and save it to .env. Later lessons use the PAT — no re-auth.
# Run:  bash 01-signup/signup.sh     (from the course/ folder)
set -euo pipefail

ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
[ -f "$ENV_FILE" ] || { echo "Create course/.env from .env.example first."; exit 1; }
set -a; . "$ENV_FILE"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_EMAIL:?}"; : "${YAKYAK_PASSWORD:?}"
field() { python3 -c "import sys,json;v=json.load(sys.stdin).get('$1');print('' if v is None else v)"; }

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

python3 - "$ENV_FILE" "$PAT" "$USER_ID" <<'PY'
import re, sys
path, token, uid = sys.argv[1:4]
txt = open(path).read()
def setk(t, k, v):
    pat = re.compile(rf'^{k}=.*$', re.M)
    return pat.sub(f'{k}={v}', t) if pat.search(t) else t + (''if t.endswith('\n')else'\n') + f'{k}={v}\n'
txt = setk(txt, 'YAKYAK_TOKEN', token)
txt = setk(txt, 'YAKYAK_USER_ID', uid)
open(path, 'w').write(txt)
PY

echo "✅ PAT saved to course/.env (it doesn't expire — no re-auth in later lessons)."
COUNT=$(curl -s "$YAKYAK_API_BASE/data/style" -H "Authorization: Bearer $PAT" | field count)
echo "Smoke test with the PAT: $COUNT styles available — you're ready for Lesson 2."
