// Lesson 7 (JavaScript, yakyak-sdk): the soundtrack two ways — (A) upload your own music
// track, then (B) let AI compose a custom score from a prompt. Forks a movie so there's
// something to score, renders once per soundtrack, prints a shareable link for each.
// Run:  npm install && node 07-soundtrack/soundtrack.js   (from course/, after Lesson 1)
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
const yak = new YakYakClient({ baseUrl: base, token, userId });
const finalUrl = async (movieId) => {
  const got = await yak.workflow.getMovie({ movieId });
  return (got.movie ?? got).finalMovieUrl || "";
};

// Render, then wait for finalMovieUrl to CHANGE (a fork starts with the source's URL).
async function renderAndWait(movieId, prevUrl) {
  await yak.workflow.exportRender({ exportRenderDto: { movieId, force: true } });
  console.log("  rendering…");
  for (let i = 0, s = "waiting"; i < 40 && s !== "completed"; i++) {
    const prog = await yak.workflow.getMovieProgress({ movieId });
    s = prog.executions?.find((e) => e.type === "movieConcat")?.status ?? "waiting";
    console.log("  render:", s);
    if (s === "failed") throw new Error("render failed");
    if (s !== "completed") await sleep(5000);
  }
  for (let i = 0; i < 36; i++) {
    const u = await finalUrl(movieId);
    if (u && u !== prevUrl) return u;
    await sleep(5000);
  }
  return finalUrl(movieId);
}

// ---- Fork a movie so we have something to score (instant; no AI scene gen) ----
const { movieId } = await yak.workflow.forkCampaign({ forkCampaignDto: {
  userId, sourceCampaignId: env.YAKYAK_TUTORIAL_CAMPAIGN_ID, sourceMovieId: env.YAKYAK_TUTORIAL_MOVIE_ID,
} });
console.log("movie:", movieId);
let url = await finalUrl(movieId); // current render; each export updates it

// ================= A) Bring your own soundtrack =================
// 1. Upload your music file — uploads.soundtrack hides the multipart POST. ✅
const track = join(ROOT, "assets/scenes/Five Years in a Turkish Prison.mp3");
const audioPath = await yak.uploads.soundtrack({ movieId, file: await readFile(track), filename: basename(track) });
console.log("uploaded your track:", audioPath.split("/").pop());
// 2. Make the uploaded track the active soundtrack, and set its volume.
await yak.workflow.setSoundtrackAudioPath({ setSoundtrackAudioDto: { movieId, audioPath } });
await yak.workflow.updateSoundtrackVolume({ soundtrackVolumeRequestDto: { movieId, volumePercentage: 80 } });
// 3. Render with your music.
console.log("Rendering with your uploaded track…");
url = await renderAndWait(movieId, url);
console.log("🎵 Your-music cut:", url);

// ================= B) AI-generated soundtrack =================
// 1. Ask YakYak to suggest a music prompt from the movie (or write your own). ✅
const suggested = (await yak.workflow.getSuggestedMusicPrompt({ movieId })).prompt;
const musicPrompt = suggested || "Upbeat tropical instrumental: ukulele, marimba and light percussion, playful and sun-soaked";
console.log("music prompt:", musicPrompt.slice(0, 70) + "…");
// 2. Clear the current soundtrack, then start AI composition. 💸
await yak.workflow.setSoundtrackAudioPath({ setSoundtrackAudioDto: { movieId, audioPath: "" } });
await yak.workflow.genMovieSoundtrack({ requestBody: { movieId, musicPrompt } });
// 3. Poll audio-tracks until the new (/audio/) score is composed.
console.log("Composing AI music (this can take a minute or two)…");
for (let i = 0; i < 60; i++) {
  const d = await yak.workflow.getAudioTracks({ movieId });
  console.log("  music:", d.soundtrackStatus ?? "waiting");
  if (d.soundtrackStatus === "completed" && (d.audioPath || "").includes("/audio/")) break;
  if (d.soundtrackStatus === "failed") { console.error("music generation failed"); process.exit(1); }
  await sleep(5000);
}
// 4. Render with the AI score (gen-movie-soundtrack already made it the active track).
console.log("Rendering with the AI score…");
url = await renderAndWait(movieId, url);
console.log("🎼 AI-score cut:", url);
