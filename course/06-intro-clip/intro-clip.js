// Lesson 6 (JavaScript, yakyak-sdk): add a pre-rendered intro clip to a movie.
// Fork a movie, upload opening.mp4 to your media library, insert it as scene 1, re-render.
// Run:  npm install && node 06-intro-clip/intro-clip.js   (from course/, after Lesson 1)
import { YakYakClient } from "yakyak-sdk";
import { readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const env = Object.fromEntries(
  readFileSync(join(ROOT, ".env"), "utf8").split("\n")
    .filter((l) => l.includes("=") && !l.trimStart().startsWith("#"))
    .map((l) => { const i = l.indexOf("="); return [l.slice(0, i).trim(), l.slice(i + 1).trim()]; })
);
const { YAKYAK_API_BASE: base, YAKYAK_TOKEN: token, YAKYAK_USER_ID: userId } = env;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const yak = new YakYakClient({ baseUrl: base, token });
const finalUrl = async (movieId) => {
  const got = await yak.workflow.getMovie({ movieId });
  return (got.movie ?? got).finalMovieUrl || "";
};

// 1. Fork a movie to add the intro to (instant; no AI generation).
const { movieId } = await yak.workflow.forkCampaign({ forkCampaignDto: {
  userId, sourceCampaignId: env.YAKYAK_TUTORIAL_CAMPAIGN_ID, sourceMovieId: env.YAKYAK_TUTORIAL_MOVIE_ID,
} });
console.log("movie:", movieId);
const oldUrl = await finalUrl(movieId); // wait for this to change after re-render

// 2. Upload the pre-rendered clip to your media library (multipart; retry on empty body).
const clip = join(ROOT, "assets/scenes/opening.mp4");
async function uploadMedia() {
  const bytes = await readFile(clip);
  for (let i = 0; i < 5; i++) {
    try {
      const fd = new FormData();
      fd.append("file", new Blob([bytes], { type: "video/mp4" }), "opening.mp4");
      fd.append("userId", userId); fd.append("filename", "opening.mp4");
      const res = await fetch(base + "/workflow/upload-user-media",
        { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: fd });
      const d = res.ok ? await res.json().catch(() => ({})) : {};
      if (d.id && d.url) return d;
    } catch { /* retry */ }
    await sleep(2000);
  }
  throw new Error("media upload failed");
}
const media = await uploadMedia();
console.log("uploaded clip:", media.id);

// 3. Insert it as the first scene (the intro).
await yak.workflow.insertMediaScene({ insertMediaSceneDto: {
  movieId, sceneNumber: 1, mediaUrl: media.url, title: "Intro", mediaId: media.id,
} });
const scenes = (await yak.workflow.getScenes({ movieId })).scenes;
console.log(`scenes now: ${scenes.length} → #1 is ${JSON.stringify(scenes[0].title)}`);

// 4. Render and wait for the new movie (finalMovieUrl changes once re-rendered).
await yak.workflow.exportRender({ exportRenderDto: { movieId, force: true } });
console.log("rendering…");
for (let i = 0, s = "waiting"; i < 30 && s !== "completed"; i++) {
  const prog = await yak.workflow.getMovieProgress({ movieId });
  s = prog.executions?.find((e) => e.type === "movieConcat")?.status ?? "waiting";
  console.log("  render:", s);
  if (s === "failed") { console.error("render failed"); process.exit(1); }
  if (s !== "completed") await sleep(5000);
}
let link = "";
for (let i = 0; i < 36; i++) {
  const u = await finalUrl(movieId);
  if (u && u !== oldUrl) { link = u; break; }
  await sleep(5000);
}
console.log("🎬 Your movie (now opening with your clip):", link || oldUrl);
