// Lesson 2 (JavaScript, yakyak-sdk): fork the Fruit Island tutorial episode and render it.
// Run:  npm install && node 02-hello-world/hello.js     (from course/, after Lesson 1)
import { YakYakClient } from "yakyak-sdk";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ENV_FILE = join(dirname(fileURLToPath(import.meta.url)), "..", ".env");
const env = Object.fromEntries(
  readFileSync(ENV_FILE, "utf8").split("\n")
    .filter((l) => l.includes("=") && !l.trimStart().startsWith("#"))
    .map((l) => { const i = l.indexOf("="); return [l.slice(0, i).trim(), l.slice(i + 1).trim()]; })
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const yak = new YakYakClient({ baseUrl: env.YAKYAK_API_BASE, token: env.YAKYAK_TOKEN });

console.log("Forking the tutorial episode into your account…");
const fork = await yak.workflow.forkCampaign({ forkCampaignDto: {
  userId: env.YAKYAK_USER_ID,
  sourceCampaignId: env.YAKYAK_TUTORIAL_CAMPAIGN_ID,
  sourceMovieId: env.YAKYAK_TUTORIAL_MOVIE_ID,
} });
const movieId = fork.movieId ?? fork.movie?.id ?? fork.id;
console.log("Forked movie:", movieId);

console.log("Rendering (stitching the scenes into the final movie)…");
// force:true — a fresh fork reports no changes, so the change-aware render
// (force:false) would be a no-op. Forcing re-stitches it into your account.
await yak.workflow.exportRender({ exportRenderDto: { movieId, force: true } });

// Render runs concat → soundtrack; finalMovieUrl is the soundtrack output, so
// wait for movieSoundtrack (not just movieConcat). Sleep first to let the backend
// flip the executions back to processing before the first poll.
let status = "waiting";
for (let i = 0; i < 60 && status !== "completed"; i++) {
  await sleep(5000);
  const prog = await yak.workflow.getMovieProgress({ movieId });
  const ex = Object.fromEntries((prog.executions ?? []).map((e) => [e.type, e.status]));
  const concat = ex.movieConcat, sound = ex.movieSoundtrack;
  status = (concat === "completed" && (sound === undefined || sound === "completed")) ? "completed"
    : ([concat, sound].includes("failed") ? "failed" : "processing");
  console.log("  render:", status);
  if (status === "failed") { console.error("Render failed."); process.exit(1); }
}

const got = await yak.workflow.getMovie({ movieId });
const movie = got.movie ?? got;
console.log("🎬 Your movie:", movie.finalMovieUrl);
