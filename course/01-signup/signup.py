"""Lesson 1 (Python, yakyak-sdk): sign up, confirm email, then mint a non-expiring
Personal Access Token (PAT) and save it to .env. If YAKYAK_PASSWORD is blank, a strong
password is generated and saved to .env (use it to sign into the web app too).
Later lessons use the PAT — no re-auth.

Run:  pip install -r requirements.txt && python 01-signup/signup.py   (from the course/ folder)
"""
import os
import re
import secrets
import string
import time

from yakyak_sdk import (ApiClient, Configuration, CreateAccessTokenDto,
                        CreateByEmailDto, DataApi, LoginByEmailDto, UsersApi)

ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")


def read_env():
    env = {}
    for line in open(ENV_FILE):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
                v = v[1:-1]
            env[k.strip()] = v
    return env


def save_env(key, value, quote=False):
    v = "'" + value + "'" if quote else value
    txt = open(ENV_FILE).read()
    pat = re.compile(rf"^{key}=.*$", re.M)
    line = f"{key}={v}"
    txt = pat.sub(lambda m: line, txt) if pat.search(txt) else txt + ("" if txt.endswith("\n") else "\n") + line + "\n"
    open(ENV_FILE, "w").write(txt)


def gen_password():
    """Length 14, including A-Z, a-z, 0-9, and a special from !@#$%^&*."""
    pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, "!@#$%^&*"]
    allc = "".join(pools)
    chars = [secrets.choice(p) for p in pools]
    chars += [secrets.choice(allc) for _ in range(14 - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


env = read_env()
base, email = env["YAKYAK_API_BASE"], env["YAKYAK_EMAIL"]
password = env.get("YAKYAK_PASSWORD", "")
if not password:
    password = gen_password()
    save_env("YAKYAK_PASSWORD", password, quote=True)
    print("🔐 Generated a password and saved it to course/.env (use it to sign into the web app too).")

anon = UsersApi(ApiClient(Configuration(host=base)))  # host is overridable

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

save_env("YAKYAK_TOKEN", pat)
save_env("YAKYAK_USER_ID", login.user_id)
print("✅ PAT saved to course/.env (it doesn't expire — no re-auth in later lessons).")

data = DataApi(ApiClient(Configuration(host=base, access_token=pat)))
styles = data.data_controller_get_styles()
count = styles.get("count") if isinstance(styles, dict) else getattr(styles, "count", "?")
print(f"Smoke test with the PAT: {count} styles available — you're ready for Lesson 2.")
