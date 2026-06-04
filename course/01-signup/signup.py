"""Lesson 1 (Python, yakyak-sdk): sign up, wait for email confirmation, save a token to .env.

Run:  pip install -r requirements.txt && python 01-signup/signup.py   (from the course/ folder)
"""
import os
import re
import time

from yakyak_sdk import (ApiClient, Configuration, CreateByEmailDto, DataApi,
                        LoginByEmailDto, UsersApi)

ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")
env = {}
for line in open(ENV_FILE):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
base, email, password = env["YAKYAK_API_BASE"], env["YAKYAK_EMAIL"], env["YAKYAK_PASSWORD"]

# base URL (host) is overridable — point it at beta or prod.
users = UsersApi(ApiClient(Configuration(host=base)))

print(f"Creating account for {email} …")
try:
    users.users_controller_create_by_email(CreateByEmailDto(email=email, password=password))
except Exception:
    pass  # may already exist

print(f"👉 Open your inbox and click the confirmation link for {email}.")
res = None
for _ in range(60):
    try:
        res = users.users_controller_login_by_email(LoginByEmailDto(email=email, password=password))
    except Exception:
        res = None
    if res and getattr(res, "token", None):
        break
    print("  waiting for confirmation… (click the link; retrying in 10s)")
    time.sleep(10)
if not (res and res.token):
    raise SystemExit("Timed out waiting for email confirmation.")


def set_key(text, key, value):
    pat = re.compile(rf"^{key}=.*$", re.M)
    return pat.sub(f"{key}={value}", text) if pat.search(text) else text + f"\n{key}={value}\n"


txt = open(ENV_FILE).read()
txt = set_key(txt, "YAKYAK_TOKEN", res.token)
txt = set_key(txt, "YAKYAK_USER_ID", res.user_id)
open(ENV_FILE, "w").write(txt)
print("✅ Confirmed. Token + user id saved to course/.env")

data = DataApi(ApiClient(Configuration(host=base, access_token=res.token)))
styles = data.data_controller_get_styles()
count = styles.get("count") if isinstance(styles, dict) else getattr(styles, "count", "?")
print(f"Smoke test: {count} styles available — you're ready for Lesson 2.")
