// Lesson 8 (JavaScript, yakyak-sdk): publish a movie to social media. Fork & render a
// movie, make sure a social network is connected (that part is browser OAuth — connect it
// in the dashboard), link the campaign, post the movie, poll until it's live, print the URL.
// Run:  npm install && node 08-social-post/social-post.js   (from course/, after Lesson 1)
import { YakYakClient } from "yakyak-sdk";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const env = Object.fromEntries(
  readFileSync(join(ROOT, ".env"), "utf8").split("\n")
    .filter((l) => l.includes("=") && !l.trimStart().startsWith("#"))
    .map((l) => { const i = l.indexOf("="); return [l.slice(0, i).trim(), l.slice(i + 1).trim()]; })
);
const { YAKYAK_API_BASE: base, YAKYAK_TOKEN: token, YAKYAK_USER_ID: userId } = env;
const webBase = base.replace("//api.", "//"); // api.beta.yakyak.ai -> beta.yakyak.ai
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const yak = new YakYakClient({ baseUrl: base, token });

// ---- Fork a movie and render it, so there's a finished video of yours to post ----
const fork = await yak.workflow.forkCampaign({ forkCampaignDto: {
  userId, sourceCampaignId: env.YAKYAK_TUTORIAL_CAMPAIGN_ID, sourceMovieId: env.YAKYAK_TUTORIAL_MOVIE_ID,
} });
const movieId = fork.movieId, campaignId = fork.campaignId;
console.log("movie:", movieId);
await yak.workflow.exportRender({ exportRenderDto: { movieId, force: true } });
console.log("rendering your cut…");
for (let i = 0, s = "waiting"; i < 40 && s !== "completed"; i++) {
  const prog = await yak.workflow.getMovieProgress({ movieId });
  s = prog.executions?.find((e) => e.type === "movieConcat")?.status ?? "waiting";
  console.log("  render:", s);
  if (s === "failed") { console.error("render failed"); process.exit(1); }
  if (s !== "completed") await sleep(5000);
}

// ---- Make sure a social network is connected (the OAuth happens in the browser) ----
// getNetworks() lists what you *can* connect; the actual hookup is an OAuth consent flow,
// so we can't script it — connect it once in the dashboard, then this polls for it.
const firstConnected = async () =>
  (await yak.social.getConnectedNetworks({ userId })).connectedNetworks?.[0] ?? null;
let net = await firstConnected();
if (!net) {
  console.log("No social network connected yet.");
  console.log(`👉 Open ${webBase}/dashboard, connect a network (e.g. YouTube) and authorize it.`);
  for (let i = 0; i < 60 && !net; i++) {
    net = await firstConnected();
    if (!net) { console.log("  waiting for a connected network… (connect it in the dashboard; retrying in 10s)"); await sleep(10000); }
  }
}
if (!net) { console.error("Timed out waiting for a connected network."); process.exit(1); }
console.log("Using connected network:", net.socialNetworkName ?? "network");

// ---- Link the campaign to the network, then post the movie ----
await yak.social.createCampaignLink({ requestBody: { campaignId, connectedNetworkId: net.id } });
console.log(`Posting to ${net.socialNetworkName ?? "network"}…`);
await yak.social.postMovieToSocialBatch({ movieId, requestBody: { connectedNetworkIds: [net.id] } });

// ---- Poll until the post succeeds (or fails); print the published URL ----
let url = "";
for (let i = 0; i < 60; i++) {
  const status = await yak.social.getMoviePostStatus({ movieId });
  const n = (status.networks ?? []).find((x) => x.connectedNetworkId === net.id);
  const last = n?.attempts?.at(-1);
  const st = last?.status ?? "pending";
  console.log("  post:", st);
  if (st === "succeeded") { url = last?.publishedUrl ?? ""; break; }
  if (st === "failed") { console.error("post failed — check the network connection and try again"); process.exit(1); }
  await sleep(5000);
}
console.log("📣 Published:", url || "<still processing — re-check post-status>");
