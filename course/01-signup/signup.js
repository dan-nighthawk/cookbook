// Lesson 1 (JavaScript, yakyak-sdk): sign up, wait for email confirmation, save a token to .env.
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
const yak = new YakYakClient({ baseUrl: base }); // base URL is overridable — point it at beta or prod

console.log(`Creating account for ${email} …`);
try { await yak.users.createByEmail({ createByEmailDto: { email, password } }); } catch { /* may already exist */ }

console.log(`👉 Open your inbox and click the confirmation link for ${email}.`);
let res = null;
for (let i = 0; i < 60; i++) {
  try { res = await yak.users.loginByEmail({ loginByEmailDto: { email, password } }); } catch { res = null; }
  if (res?.token) break;
  console.log("  waiting for confirmation… (click the link; retrying in 10s)");
  await sleep(10_000);
}
if (!res?.token) { console.error("Timed out waiting for email confirmation."); process.exit(1); }

let txt = readFileSync(ENV_FILE, "utf8");
for (const [k, v] of [["YAKYAK_TOKEN", res.token], ["YAKYAK_USER_ID", res.userId]]) {
  const re = new RegExp(`^${k}=.*$`, "m");
  txt = re.test(txt) ? txt.replace(re, `${k}=${v}`) : `${txt}\n${k}=${v}\n`;
}
writeFileSync(ENV_FILE, txt);
console.log("✅ Confirmed. Token + user id saved to course/.env");

const styles = await new YakYakClient({ baseUrl: base, token: res.token }).data.getStyles();
console.log(`Smoke test: ${styles.count} styles available — you're ready for Lesson 2.`);
