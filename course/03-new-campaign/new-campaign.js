// Lesson 3 (JavaScript, yakyak-sdk): create your own campaign from a prompt, with a
// custom cast (uploaded portraits), then let YakYak write the screenplay — generating
// every scene (AI still + Ken Burns + subtitles) — and render the movie.
// Run:  npm install && node 03-new-campaign/new-campaign.js   (from course/, after Lesson 1)
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
const yak = new YakYakClient({ baseUrl: base, token, userId });

async function waitMovie(movieId, type) { // poll a movie-level execution until it completes
  for (let i = 0; i < 120; i++) {
    const prog = await yak.workflow.getMovieProgress({ movieId });
    const s = prog.executions?.find((e) => e.type === type)?.status ?? "waiting";
    console.log(`  ${type}: ${s}`);
    if (s === "completed") return;
    if (s === "failed") throw new Error(`${type} failed`);
    await sleep(5000);
  }
  throw new Error(`${type} timed out`);
}

// 1. Style + 2. campaign + 3. movie
const styles = (await yak.data.getStyles()).styles;
const styleId = (styles.find((s) => s.label.includes("Cartoon")) ?? styles[0]).id;
const { campaignId } = await yak.workflow.createCampaign({ createCampaignDto: {
  userId, prompt: "Fruit Island Reblended — sentient fruits outwit a smoothie-obsessed chef",
  styleId, aspectRatio: "1:1", animationType: "kenburns", mode: "pro",
} });
console.log("campaign:", campaignId);
const { movieId } = await yak.workflow.startCampaign({ startCampaignDto: { campaignId } });
console.log("movie:", movieId);

// 4. Upload portraits (your own art, no AI image gen) — uploads.castImage hides the multipart POST
const imgs = (await import("node:fs")).readdirSync(join(ROOT, "assets/cast")).filter((f) => f.endsWith(".png"));
const heroImg = await yak.uploads.castImage({ campaignId, file: await readFile(join(ROOT, "assets/cast", imgs[0])), filename: imgs[0] });
const villainImg = await yak.uploads.castImage({ campaignId, file: await readFile(join(ROOT, "assets/cast", imgs[1])), filename: imgs[1] });
console.log("portraits uploaded");

// 5. Custom cast (imageUrl links each portrait) + voices/fonts
await yak.workflow.saveMovieCustomCast({ saveMovieCustomCastDto: { movieId, characters: [
  { name: "Mango Max", role: "Protagonist", description: "Our sweet lovable mango hero", imageUrl: heroImg, sortOrder: 0 },
  { name: "Chef Blendero", role: "Antagonist", description: "The evil chef who wants to blend every fruit into a smoothie", imageUrl: villainImg, sortOrder: 1 },
] } });
const cast = (await yak.workflow.getCast({ movieId })).cast;
const idOf = (name) => cast.find((c) => c.name === name).id;
await yak.workflow.setCast({ setCastDto: { movieId, cast: [
  { id: idOf("Mango Max"), name: "Mango Max", role: "Protagonist", description: "Our sweet lovable mango hero", voiceId: "pNInz6obpgDQGcFmaJgB", fontFamily: "Bangers", color: "#e0b000" },
  { id: idOf("Chef Blendero"), name: "Chef Blendero", role: "Antagonist", description: "The evil chef", voiceId: "VR6AewLTigWG4xSOukaG", fontFamily: "Bangers", color: "#640080" },
] } });

// 6. Render the custom cast, then let YakYak write the screenplay. genMovieScreenplay
//    writes every scene from your premise AND renders each one — AI still (💸) → Ken
//    Burns → subtitles — server-side. Wait for the movieScreenplay execution to finish.
await yak.workflow.genMovieCast({ genMovieCastDto: { movieId } });
console.log("writing the screenplay & generating scenes (💸 one AI still per scene, takes a few minutes)…");
await yak.workflow.genMovieScreenplay({ genMovieScreenplayRequestDto: { movieId } });
await waitMovie(movieId, "movieScreenplay");

// 7. Pick an existing soundtrack (e.g. Fruit Island), if available
const list = await yak.workflow.getAvailableSoundtracks({ movieId });
const tracks = Array.isArray(list) ? list : list.soundtracks ?? [];
if (tracks.length) {
  await yak.workflow.setSoundtrackAudioPath({ setSoundtrackAudioDto: { movieId, audioPath: tracks[0].audioPath } });
  console.log("soundtrack set");
} else console.log("no existing soundtrack — rendering without one");

// 8. Render → link
await yak.workflow.exportRender({ exportRenderDto: { movieId, force: true } });
console.log("rendering…");
for (let i = 0, s = "waiting"; i < 60 && s !== "completed"; i++) {
  const prog = await yak.workflow.getMovieProgress({ movieId });
  s = prog.executions?.find((e) => e.type === "movieConcat")?.status ?? "waiting";
  console.log("  render:", s);
  if (s === "failed") { console.error("render failed"); process.exit(1); }
  if (s !== "completed") await sleep(5000);
}
// The final URL appears once the soundtrack is muxed in (just after concat).
let link = "";
for (let i = 0; i < 36 && !link; i++) {
  const m = (await yak.workflow.getMovie({ movieId }));
  const mv = m.movie ?? m;
  link = mv.finalMovieUrl || mv.soundtrackedMovieUrl || mv.concatMovieUrl || "";
  if (!link) await sleep(5000);
}
console.log("🎬 Your movie:", link);
