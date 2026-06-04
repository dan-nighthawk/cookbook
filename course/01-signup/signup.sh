#!/usr/bin/env bash
# Lesson 1 (bash/curl): sign up, wait for email confirmation, save a token to .env.
# Run:  bash 01-signup/signup.sh     (from the course/ folder)
set -euo pipefail

ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
[ -f "$ENV_FILE" ] || { echo "Create course/.env from .env.example first."; exit 1; }
set -a; . "$ENV_FILE"; set +a
: "${YAKYAK_API_BASE:?set YAKYAK_API_BASE in .env}"
: "${YAKYAK_EMAIL:?set YAKYAK_EMAIL in .env}"
: "${YAKYAK_PASSWORD:?set YAKYAK_PASSWORD in .env}"

field() { python3 -c "import sys,json;v=json.load(sys.stdin).get('$1');print('' if v is None else v)"; }

echo "Creating account for $YAKYAK_EMAIL …"
curl -s -X POST "$YAKYAK_API_BASE/users/create-by-email" -H "Content-Type: application/json" \
  -d "{\"email\":\"$YAKYAK_EMAIL\",\"password\":\"$YAKYAK_PASSWORD\"}" >/dev/null || true

echo "👉 Open your inbox and click the confirmation link for $YAKYAK_EMAIL."
TOKEN=""; USER_ID=""
for _ in $(seq 1 60); do
  RESP=$(curl -s -X POST "$YAKYAK_API_BASE/users/login-by-email" -H "Content-Type: application/json" \
    -d "{\"email\":\"$YAKYAK_EMAIL\",\"password\":\"$YAKYAK_PASSWORD\"}")
  TOKEN=$(printf '%s' "$RESP" | field token)
  if [ -n "$TOKEN" ]; then USER_ID=$(printf '%s' "$RESP" | field userId); break; fi
  echo "  waiting for confirmation… (click the link; retrying in 10s)"
  sleep 10
done
[ -n "$TOKEN" ] || { echo "Timed out waiting for email confirmation."; exit 1; }

python3 - "$ENV_FILE" "$TOKEN" "$USER_ID" <<'PY'
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

echo "✅ Confirmed. Token + user id saved to course/.env"
COUNT=$(curl -s "$YAKYAK_API_BASE/data/style" -H "Authorization: Bearer $TOKEN" | field count)
echo "Smoke test: $COUNT styles available — you're ready for Lesson 2."
