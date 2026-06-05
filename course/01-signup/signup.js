// Lesson 1 (JavaScript, yakyak-sdk): sign up, confirm email, then mint a non-expiring
// Personal Access Token (PAT) and save it to .env. Later lessons use the PAT — no re-auth.
// Run:  npm install && node 01-signup/signup.js     (from the course/ folder)
import { YakYakClient } from "yakyak-sdk";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ENV_FILE = join(dirname(fileURLToPath(import.meta.url)), "..", ".env");
const env = Object.fromEntries(
  readFileSync(ENV_FILE, "utf8").split("\n")
    .filter((l) => l.includes("=") && !l.trimStart().startsWith("#"))
    .map((l) => { const i = l.indexOf("="); return [l.slice(0, i).trim(), l.slice(i + 1).trim()]; })
);
const { YAKYAK_API_BASE: base, YAKYAK_EMAIL: email, YAKYAK_PASSWORD: password } = env;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const anon = new YakYakClient({ baseUrl: base }); // base URL is overridable (beta vs prod)

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

let txt = readFileSync(ENV_FILE, "utf8");
for (const [k, v] of [["YAKYAK_TOKEN", pat], ["YAKYAK_USER_ID", login.userId]]) {
  const re = new RegExp(`^${k}=.*$`, "m");
  txt = re.test(txt) ? txt.replace(re, `${k}=${v}`) : `${txt}\n${k}=${v}\n`;
}
writeFileSync(ENV_FILE, txt);
console.log("✅ PAT saved to course/.env (it doesn't expire — no re-auth in later lessons).");

const styles = await new YakYakClient({ baseUrl: base, token: pat }).data.getStyles();
console.log(`Smoke test with the PAT: ${styles.count} styles available — you're ready for Lesson 2.`);
