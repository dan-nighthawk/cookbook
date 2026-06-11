// Lesson 1 (JavaScript, yakyak-sdk): sign up, confirm email, then mint a non-expiring
// Personal Access Token (PAT) and save it to .env. If YAKYAK_PASSWORD is blank, a strong
// password is generated and saved to .env (use it to sign into the web app too).
// Run:  npm install && node 01-signup/signup.js     (from the course/ folder)
import { YakYakClient } from "yakyak-sdk";
import { readFileSync, writeFileSync } from "node:fs";
import { randomInt } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ENV_FILE = join(dirname(fileURLToPath(import.meta.url)), "..", ".env");
function readEnv() {
  return Object.fromEntries(
    readFileSync(ENV_FILE, "utf8").split("\n")
      .filter((l) => l.includes("=") && !l.trimStart().startsWith("#"))
      .map((l) => {
        const i = l.indexOf("=");
        let v = l.slice(i + 1).trim();
        if (v.length >= 2 && ((v[0] === "'" && v.at(-1) === "'") || (v[0] === '"' && v.at(-1) === '"'))) v = v.slice(1, -1);
        return [l.slice(0, i).trim(), v];
      })
  );
}
function setEnv(key, value, quote = false) {
  const v = quote ? `'${value}'` : value;
  let txt = readFileSync(ENV_FILE, "utf8");
  const re = new RegExp(`^${key}=.*$`, "m");
  const line = `${key}=${v}`;
  txt = re.test(txt) ? txt.replace(re, () => line) : `${txt}${txt.endsWith("\n") ? "" : "\n"}${line}\n`;
  writeFileSync(ENV_FILE, txt);
}
// Strong password: length 14 incl. A-Z, a-z, 0-9, and a special from !@#$%^&*.
function genPassword() {
  const U = "ABCDEFGHIJKLMNOPQRSTUVWXYZ", L = "abcdefghijklmnopqrstuvwxyz", D = "0123456789", S = "!@#$%^&*";
  const pools = [U, L, D, S], all = U + L + D + S, pick = (s) => s[randomInt(s.length)];
  const chars = pools.map(pick);
  while (chars.length < 14) chars.push(pick(all));
  for (let i = chars.length - 1; i > 0; i--) { const j = randomInt(i + 1); [chars[i], chars[j]] = [chars[j], chars[i]]; }
  return chars.join("");
}

const env = readEnv();
const base = env.YAKYAK_API_BASE, email = env.YAKYAK_EMAIL;
let password = env.YAKYAK_PASSWORD;
if (!password) {
  password = genPassword();
  setEnv("YAKYAK_PASSWORD", password, true);
  console.log("🔐 Generated a password and saved it to course/.env (use it to sign into the web app too).");
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const anon = new YakYakClient({ baseUrl: base }); // base URL is overridable

console.log(`Creating account for ${email} …`);
try { await anon.users.createByEmail({ createByEmailDto: { email, password } }); } catch { /* may already exist */ }

// Confirmation is a link click; login only returns a token once confirmed, so poll it.
console.log(`👉 Open your inbox and click the confirmation link for ${email}.`);
let login = null;
for (let i = 0; i < 60; i++) {
  try { login = await anon.users.loginByEmail({ loginByEmailDto: { email, password } }); } catch { login = null; }
  if (login?.token) break;
  console.log("  waiting for confirmation… (click the link; retrying in 10s)");
  await sleep(10_000);
}
if (!login?.token) { console.error("Timed out waiting for email confirmation."); process.exit(1); }

// Mint a non-expiring Personal Access Token using the (short-lived) session token.
console.log("Creating a Personal Access Token…");
const yak = new YakYakClient({ baseUrl: base, token: login.token });
const { token: pat } = await yak.users.createAccessToken({ createAccessTokenDto: {
  name: "YakYak course",
  scopes: ["video_creation", "social_publishing", "account_management"],
} });
if (!pat) { console.error("Failed to create access token."); process.exit(1); }

setEnv("YAKYAK_TOKEN", pat);
setEnv("YAKYAK_USER_ID", login.userId);
console.log("✅ PAT saved to course/.env (it doesn't expire — no re-auth in later lessons).");

const styles = await new YakYakClient({ baseUrl: base, token: pat }).data.getStyles();
console.log(`Smoke test with the PAT: ${styles.count} styles available — you're ready for Lesson 2.`);
