# Lesson 1 — Sign up & get your token

Every call (except a few public reads) needs a **Bearer JWT**. You get one by
creating an account and **confirming your email**, or by logging in to an account
that's already confirmed.

> Prerequisites: a base URL and credentials exported as in the [setup](README.md#setup).

## 1. Create your account

`POST /users/create-by-email` creates the user and emails a **4-digit confirmation
code**. The response tells you whether the account still needs confirming.

```bash
curl -s -X POST "$YAKYAK_API_BASE/users/create-by-email" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$YAKYAK_EMAIL\",\"password\":\"$YAKYAK_PASSWORD\"}"
```

```js
const created = await (await fetch(process.env.YAKYAK_API_BASE + "/users/create-by-email", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: process.env.YAKYAK_EMAIL, password: process.env.YAKYAK_PASSWORD }),
})).json();
console.log(created); // { status, userId, email, isConfirmed, token? }
```

```python
import os, requests
created = requests.post(os.environ["YAKYAK_API_BASE"] + "/users/create-by-email",
    json={"email": os.environ["YAKYAK_EMAIL"], "password": os.environ["YAKYAK_PASSWORD"]}).json()
print(created)  # { status, userId, email, isConfirmed, token? }
```

Response:

```json
{ "status": "user_created", "userId": "…", "email": "you@example.com", "isConfirmed": false }
```

- `isConfirmed: false` → **check your inbox** for the 4-digit code and confirm (step 2).
- Already confirmed? You'll get `isConfirmed: true` and a `token` — skip to step 3, or
  just [log in](#log-in-later).

## 2. Confirm your email

Read the code from your inbox and send it to `POST /users/confirm-email`. The
response returns your **token** and **userId**.

```bash
read -p "Enter the 4-digit code from your email: " CODE
curl -s -X POST "$YAKYAK_API_BASE/users/confirm-email" \
  -H "Content-Type: application/json" -d "{\"code\":\"$CODE\"}"
```

```js
import { createInterface } from "node:readline/promises";
const rl = createInterface({ input: process.stdin, output: process.stdout });
const code = await rl.question("Enter the 4-digit code from your email: ");
rl.close();
const confirmed = await (await fetch(process.env.YAKYAK_API_BASE + "/users/confirm-email", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ code: code.trim() }),
})).json();
console.log(confirmed); // { confirmed: true, token, userId, email }
```

```python
code = input("Enter the 4-digit code from your email: ").strip()
confirmed = requests.post(os.environ["YAKYAK_API_BASE"] + "/users/confirm-email",
    json={"code": code}).json()
print(confirmed)  # { "confirmed": true, "token": "...", "userId": "...", "email": "..." }
```

## 3. Save your token & user id

Export the `token` and `userId` — almost every write call needs both.

```bash
# paste the values from the confirm-email response
export YAKYAK_TOKEN="eyJhbGciOi…"
export YAKYAK_USER_ID="…"
```

```js
process.env.YAKYAK_TOKEN = confirmed.token;
process.env.YAKYAK_USER_ID = confirmed.userId;
```

```python
os.environ["YAKYAK_TOKEN"] = confirmed["token"]
os.environ["YAKYAK_USER_ID"] = confirmed["userId"]
```

## 4. Smoke-test it

Hit a simple authenticated read — the list of visual styles you'll choose from next.

```bash
curl -s "$YAKYAK_API_BASE/data/style" -H "Authorization: Bearer $YAKYAK_TOKEN" \
  | head -c 300
```

```js
const styles = await (await fetch(process.env.YAKYAK_API_BASE + "/data/style",
  { headers: { Authorization: `Bearer ${process.env.YAKYAK_TOKEN}` } })).json();
console.log(styles.count, "styles:", styles.styles.map(s => s.label).join(", "));
```

```python
styles = requests.get(os.environ["YAKYAK_API_BASE"] + "/data/style",
    headers={"Authorization": f"Bearer {os.environ['YAKYAK_TOKEN']}"}).json()
print(styles["count"], "styles:", ", ".join(s["label"] for s in styles["styles"]))
```

A `200` with a list of styles means you're in. 🎉

## Log in later

Once confirmed, swap signup for `POST /users/login-by-email` to get a fresh token:

```bash
curl -s -X POST "$YAKYAK_API_BASE/users/login-by-email" -H "Content-Type: application/json" \
  -d "{\"email\":\"$YAKYAK_EMAIL\",\"password\":\"$YAKYAK_PASSWORD\"}"
# -> { "token": "...", "status": "success", "userId": "...", "email": "..." }
```

## Troubleshooting

| Symptom | Cause & fix |
|---------|-------------|
| Login returns `status:"failure"`, *"account not confirmed"* | You haven't confirmed yet — do step 2 with the emailed code. |
| A write call fails right after signup | Your email isn't confirmed. Confirm first, then retry. |
| `403 Resource ownership required` | Include `userId` in the request body (you'll see this from Lesson 2 on). |
| `401` | Token missing/expired — log in again for a fresh one. |

---

**Next:** [Lesson 2 — Hello, world: your first movie](02-hello-world.md) ⭐
