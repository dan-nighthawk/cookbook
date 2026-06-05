// Lesson 5 (JavaScript, yakyak-sdk): bring your own pre-rendered still, animate it
// with Kling AI video, and voice the scene with the cinematic "Narrator" from Lesson 4.
//   create-scene(generate:false) → upload-scene-image → regen subtitle (voice-over)
//   → rerun from:movie (Kling) → rerun from:burn (subtitles) → render.
// Run:  npm install && node 05-byo-image/byo-image.js   (from course/, after Lesson 1)
import { YakYakClient } from "yakyak-sdk";
import { readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join, basename } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const env = Object.fromEntries(
  readFileSync(join(ROOT, ".env"), "utf8").split("\n")
    .filter((l) => l.includes("=") && !l.trimStart().startsWith("#"))
    .map((l) => { const i = l.indexOf("="); return [l.slice(0, i).trim(), l.slice(i + 1).trim()]; })
);
const { YAKYAK_API_BASE: base, YAKYAK_TOKEN: token, YAKYAK_USER_ID: userId } = env;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const yak = new YakYakClient({ baseUrl: base, token });

const IMAGE = join(ROOT, "assets/scenes/asian-fruit-lady.jpeg");   // <- your own pre-rendered still
const DIALOGUE = "Once upon a time there was a lady who thought her fruits were alive";

// Upload a scene image straight over HTTP (multipart) — same trick Lesson 3/4 use for portraits.
async function uploadSceneImage(path, sceneId) {
  const bytes = await readFile(path);
  for (let i = 0; i < 5; i++) {
    try {
      const fd = new FormData();
      fd.append("file", new Blob([bytes], { type: "image/jpeg" }), basename(path));
      fd.append("sceneId", sceneId);
      const res = await fetch(base + "/workflow/upload-scene-image",
        { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: fd });
      const url = res.ok ? (await res.json().catch(() => ({}))).imageUrl : null;
      if (url) return url;
    } catch { /* retry */ }
    await sleep(2000);
  }
  throw new Error(`scene image upload failed for ${path}`);
}
// Poll one scene asset's status straight off get-movie.
async function sceneStatus(movieId, sceneId, key) {
  const m = await yak.workflow.getMovie({ movieId });
  const mv = m.movie ?? m;
  const sc = (mv.scene ?? mv.scenes ?? []).find((s) => s.id === sceneId) ?? {};
  return (sc[key] ?? {}).status ?? "waiting";
}
async function waitAsset(movieId, sceneId, key, label) {
  for (let i = 0; i < 120; i++) {
    const s = await sceneStatus(movieId, sceneId, key);
    console.log(`  ${label}: ${s}`);
    if (s === "completed") return;
    if (s === "failed") throw new Error(`${label} failed`);
    await sleep(5000);
  }
  throw new Error(`${label} timed out`);
}

// ---- Setup: a campaign + a Narrator with the cinematic "Cinema" voice (recap of Lesson 4) ----
const styles = (await yak.data.getStyles()).styles;
const styleId = (styles.find((s) => s.label.includes("Cartoon")) ?? styles[0]).id;
const { campaignId } = await yak.workflow.createCampaign({ createCampaignDto: {
  userId, prompt: "A whimsical fruit lady who is convinced her fruits are alive",
  styleId, aspectRatio: "1:1", animationType: "kenburns", mode: "pro",
} });
const { movieId } = await yak.workflow.startCampaign({ startCampaignDto: { campaignId } });
console.log("campaign:", campaignId, "\nmovie:", movieId);

const voices = (await yak.data.getVoices()).voices;
const cinema = (voices.find((v) => v.voiceName === "Cinema") || { voiceId: "Caw0sfpaJco97FKdXypJ" }).voiceId;
await yak.workflow.saveMovieCustomCast({ saveMovieCustomCastDto: { movieId, characters: [
  { name: "Narrator", role: "Supporting Character", description: "A dramatic voice that narrates the story", sortOrder: 0 },
] } });
const narratorId = (await yak.workflow.getCast({ movieId })).cast.find((c) => c.name === "Narrator").id;
await yak.workflow.setCast({ setCastDto: { movieId, cast: [
  { id: narratorId, name: "Narrator", role: "Supporting Character", voiceId: cinema, fontFamily: "Bangers", color: "#00abad" },
] } });
console.log("Narrator ready (cinematic voice).");

// ---- 1) Turn on AI animation (Kling) for this campaign 💸 ----
await yak.workflow.updateCampaignSettings({ updateCampaignSettingsDto: { campaignId, aspectRatio: "1:1", animationType: "kling" } });
console.log("Animation set to Kling (AI video).");

// ---- 2) Create a scene WITHOUT generating art (generate:false) — we bring our own ----
const scene = await yak.workflow.createScene({ createSceneDto: {
  movieId, sceneNumber: 1, title: "The Fruit Lady", story: "The fruit lady with her fruits",
  dialogue: DIALOGUE, leadCast: "Narrator", generate: false,
} });
const sceneId = scene.id;
console.log("scene:", sceneId);

// ---- 3) Upload your own pre-rendered still as the scene image ✅ ----
const imgUrl = await uploadSceneImage(IMAGE, sceneId);
console.log("uploaded your image:", imgUrl);

// ---- 4) Voice the scene: generate the Narrator's voice-over + captions ✅ ----
await yak.workflow.regenSceneAsset({ requestBody: { sceneId, asset: "subtitle", from: "subtitle" } });
console.log("Narrating in the cinematic voice…");
await waitAsset(movieId, sceneId, "sceneSubtitleMovie", "voice-over");

// ---- 5) Animate your still with Kling AI video 💸 ----
await yak.workflow.rerunScene({ rerunSceneDto: { sceneId, from: "movie" } });
console.log("Kling is animating your image (this can take a few minutes)…");
await waitAsset(movieId, sceneId, "sceneMovie", "kling");

// ---- 6) Burn the subtitles into the animated clip ✅ ----
await yak.workflow.rerunScene({ rerunSceneDto: { sceneId, from: "burn" } });
console.log("Burning subtitles…");
await waitAsset(movieId, sceneId, "sceneBurnSubtitle", "subtitles");

// ---- 7) Render → shareable link ----
await yak.workflow.exportRender({ exportRenderDto: { movieId, force: true } });
console.log("rendering…");
for (let i = 0, s = "waiting"; i < 60 && s !== "completed"; i++) {
  const prog = await yak.workflow.getMovieProgress({ movieId });
  s = prog.executions?.find((e) => e.type === "movieConcat")?.status ?? "waiting";
  console.log("  render:", s);
  if (s === "failed") { console.error("render failed"); process.exit(1); }
  if (s !== "completed") await sleep(5000);
}
let link = "";
for (let i = 0; i < 36 && !link; i++) {
  const mv = (await yak.workflow.getMovie({ movieId }));
  const m = mv.movie ?? mv;
  link = m.finalMovieUrl || m.soundtrackedMovieUrl || m.concatMovieUrl || "";
  if (!link) await sleep(5000);
}
console.log("🎬 Your movie:", link);
