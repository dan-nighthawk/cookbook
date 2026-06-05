// Lesson 4 (JavaScript, yakyak-sdk): grow & edit a movie — generate an AI screenplay,
// then 1) delete a scene, 2) add a Narrator (cinematic voice), 3) add an AI Guru.
// Run:  npm install && node 04-edit-movie/edit-movie.js   (from course/, after Lesson 1)
import { YakYakClient } from "yakyak-sdk";
import { readFileSync } from "node:fs";
import { readFile, readdir } from "node:fs/promises";
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

async function uploadPortrait(path, campaignId) {
  const bytes = await readFile(path);
  for (let i = 0; i < 5; i++) {
    try {
      const fd = new FormData();
      fd.append("file", new Blob([bytes], { type: "image/png" }), basename(path));
      fd.append("userId", userId); fd.append("campaignId", campaignId);
      const res = await fetch(base + "/workflow/upload-cast-character-image",
        { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: fd });
      const url = res.ok ? (await res.json().catch(() => ({}))).imageUrl : null;
      if (url) return url;
    } catch { /* retry */ }
    await sleep(2000);
  }
  throw new Error(`upload failed for ${path}`);
}
async function waitMovie(movieId, type) {
  for (let i = 0; i < 60; i++) {
    const prog = await yak.workflow.getMovieProgress({ movieId });
    const s = prog.executions?.find((e) => e.type === type)?.status ?? "waiting";
    console.log(`  ${type}: ${s}`);
    if (s === "completed") return;
    if (s === "failed") throw new Error(`${type} failed`);
    await sleep(5000);
  }
  throw new Error(`${type} timed out`);
}
const isGuru = (c) => /gur|guide/i.test(c.role || "");

// ---- Setup: campaign + custom cast + AI screenplay (recap of Lessons 1–3) ----
const styles = (await yak.data.getStyles()).styles;
const styleId = (styles.find((s) => s.label.includes("Cartoon")) ?? styles[0]).id;
const { campaignId } = await yak.workflow.createCampaign({ createCampaignDto: {
  userId, prompt: "Fruits on a tropical island outwit the smoothie-obsessed Chef Blendero",
  styleId, aspectRatio: "1:1", animationType: "kenburns", mode: "pro",
} });
const { movieId } = await yak.workflow.startCampaign({ startCampaignDto: { campaignId } });
console.log("movie:", movieId);
const castImgs = (await readdir(join(ROOT, "assets/cast"))).filter((f) => f.endsWith(".png"));
const heroImg = await uploadPortrait(join(ROOT, "assets/cast", castImgs[0]), campaignId);
const villainImg = await uploadPortrait(join(ROOT, "assets/cast", castImgs[1]), campaignId);
const baseCast = [
  { name: "Mango Max", role: "Protagonist", description: "Our charming mango hero", imageUrl: heroImg, sortOrder: 0 },
  { name: "Chef Blendero", role: "Antagonist", description: "The evil chef who blends fruit into smoothies", imageUrl: villainImg, sortOrder: 1 },
];
await yak.workflow.saveMovieCustomCast({ saveMovieCustomCastDto: { movieId, characters: baseCast } });
console.log("Generating an AI screenplay…");
await yak.workflow.genMovieScreenplay({ genMovieScreenplayRequestDto: { movieId } });
await waitMovie(movieId, "movieScreenplay");

// ---- 1) Delete a scene you don't need (keep the outro, which has no dialogue) ----
let scenes = (await yak.workflow.getScenes({ movieId })).scenes;
const story = scenes.filter((s) => (s.dialogue || "").trim());
console.log(`Deleting one AI scene (${story.at(-1).id})…`);
await yak.workflow.deleteScene({ deleteSceneDto: { sceneId: story.at(-1).id } });
console.log("  scenes now:", (await yak.workflow.getScenes({ movieId })).scenes.length);

// ---- 2) Add a Narrator with the cinematic "Cinema" voice ----
const voices = (await yak.data.getVoices()).voices;
const cinema = (voices.find((v) => v.voiceName === "Cinema") || { voiceId: "Caw0sfpaJco97FKdXypJ" }).voiceId;
await yak.workflow.saveMovieCustomCast({ saveMovieCustomCastDto: { movieId, characters: [
  ...baseCast,
  { name: "Narrator", role: "Supporting Character", description: "A dramatic voice that narrates the story", sortOrder: 2 },
] } });
const byName = Object.fromEntries((await yak.workflow.getCast({ movieId })).cast.map((c) => [c.name, c.id]));
await yak.workflow.setCast({ setCastDto: { movieId, cast: [
  { id: byName["Mango Max"], name: "Mango Max", role: "Protagonist", voiceId: "pNInz6obpgDQGcFmaJgB", fontFamily: "Bangers", color: "#db9600" },
  { id: byName["Chef Blendero"], name: "Chef Blendero", role: "Antagonist", voiceId: "VR6AewLTigWG4xSOukaG", fontFamily: "Bangers", color: "#9200c7" },
  { id: byName["Narrator"], name: "Narrator", role: "Supporting Character", voiceId: cinema, fontFamily: "Bangers", color: "#00abad" },
] } });
console.log("Added Narrator (cinematic voice).");

// ---- 3) Add an AI-generated Guru, then generate its portrait 💸 ----
console.log("Generating an AI Guru…");
await yak.workflow.genMovieCast({ genMovieCastDto: { movieId, roleCounts: { protagonists: 0, antagonists: 0, gurus: 1, supporting: 0 } } });
// The guru appears in the cast a moment after generation; poll until it shows up.
let guru = null;
for (let i = 0; i < 36 && !guru; i++) {
  guru = (await yak.workflow.getCast({ movieId })).cast.find(isGuru);
  if (!guru) { console.log("  waiting for the AI guru…"); await sleep(5000); }
}
if (!guru) throw new Error("guru was not generated");
console.log("  guru:", guru.name);
await yak.workflow.genCustomCastImage({ genCustomCastImageDto: {
  movieId, characterName: guru.name, description: guru.description || "A wise guide who helps the fruits escape",
} });
console.log("Generating the Guru's portrait…");
for (let i = 0; i < 36; i++) {
  const g = (await yak.workflow.getCast({ movieId })).cast.find(isGuru);
  console.log("  guru portrait:", g.imageUrl ? "Y" : "N");
  if (g.imageUrl) break;
  await sleep(5000);
}

console.log("✅ Final cast:");
for (const c of (await yak.workflow.getCast({ movieId })).cast) {
  console.log(`  - ${c.name} · ${c.role} · ${c.imageUrl ? "portrait ✓" : "no portrait"}`);
}
console.log("Re-run export-render (as in Lesson 2/3) to watch the edited movie.");
