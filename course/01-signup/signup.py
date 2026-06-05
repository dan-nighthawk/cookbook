"""Lesson 1 (Python, yakyak-sdk): sign up, confirm email, then mint a non-expiring
Personal Access Token (PAT) and save it to .env. Later lessons use the PAT — no re-auth.

Run:  pip install -r requirements.txt && python 01-signup/signup.py   (from the course/ folder)
"""
import os
import re
import time

from yakyak_sdk import (ApiClient, Configuration, CreateAccessTokenDto,
                        CreateByEmailDto, DataApi, LoginByEmailDto, UsersApi)

ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")
env = {}
for line in open(ENV_FILE):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
base, email, password = env["YAKYAK_API_BASE"], env["YAKYAK_EMAIL"], env["YAKYAK_PASSWORD"]

anon = UsersApi(ApiClient(Configuration(host=base)))  # host is overridable (beta vs prod)

print(f"Creating account for {email} …")
try:
    anon.users_controller_create_by_email(CreateByEmailDto(email=email, password=password))
except Exception:
    pass  # may already exist

# Confirmation is a link click; login only returns a token once confirmed, so poll it.
print(f"👉 Open your inbox and click the confirmation link for {email}.")
login = None
for _ in range(60):
    try:
        login = anon.users_controller_login_by_email(LoginByEmailDto(email=email, password=password))
    except Exception:
        login = None
    if login and getattr(login, "token", None):
        break
    print("  waiting for confirmation… (click the link; retrying in 10s)")
    time.sleep(10)
if not (login and login.token):
    raise SystemExit("Timed out waiting for email confirmation.")

# Mint a non-expiring Personal Access Token using the (short-lived) session token.
print("Creating a Personal Access Token…")
users = UsersApi(ApiClient(Configuration(host=base, access_token=login.token)))
created = users.users_controller_create_access_token(CreateAccessTokenDto.from_dict({
    "name": "YakYak course",
    "scopes": ["video_creation", "social_publishing", "account_management"],
}))
pat = created["token"] if isinstance(created, dict) else created.to_dict()["token"]


def set_key(text, key, value):
    pat_re = re.compile(rf"^{key}=.*$", re.M)
    return pat_re.sub(f"{key}={value}", text) if pat_re.search(text) else text + f"\n{key}={value}\n"


txt = open(ENV_FILE).read()
txt = set_key(txt, "YAKYAK_TOKEN", pat)
txt = set_key(txt, "YAKYAK_USER_ID", login.user_id)
open(ENV_FILE, "w").write(txt)
print("✅ PAT saved to course/.env (it doesn't expire — no re-auth in later lessons).")

data = DataApi(ApiClient(Configuration(host=base, access_token=pat)))
styles = data.data_controller_get_styles()
count = styles.get("count") if isinstance(styles, dict) else getattr(styles, "count", "?")
print(f"Smoke test with the PAT: {count} styles available — you're ready for Lesson 2.")
