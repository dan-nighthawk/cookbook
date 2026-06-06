# Lesson 8 — Publish to social

You've made a movie — now ship it. This lesson connects a social network, links it to a
campaign, and **posts the rendered movie**, then polls until it's live and prints the
published URL.

**▶ Here's the actual result of this flow, live on YouTube:**
<https://www.youtube.com/watch?v=TBq5_CwhxdI>

That video was posted by the exact `post-movie-batch` call below (channel *Dan
Nighthawk*) — its `publishedUrl` came straight out of `GET /social/post-status`.

> Needs `YAKYAK_TOKEN` + `YAKYAK_USER_ID` from [Lesson 1](../01-signup/) (the PAT carries
> the `social_publishing` scope), plus `YAKYAK_TUTORIAL_CAMPAIGN_ID` /
> `YAKYAK_TUTORIAL_MOVIE_ID` (the movie it forks & renders to post — same as Lessons 6–7).

## Connecting a network is a browser step

Hooking up YouTube (or Instagram, TikTok, LinkedIn, …) is an **OAuth consent flow** — you
authorize YakYak in your browser, so it can't be done from a script. Do it **once** in the
web app:

1. Open the **YakYak dashboard** → connect a network (e.g. YouTube) and authorize it.
2. Under the hood that runs `GET /social/network-auth/{network}` → provider consent →
   `POST /social/connect-network` and a connected network appears.

The scripts below **poll `GET /social/connected-networks/{userId}`** until one shows up
(the same "do it in the browser, then we continue" pattern as Lesson 1's email
confirmation), so just run the script and connect the network when prompted.

As always, this can be done entirely in the **web app (GUI)**, or via **REST** (`curl`) /
the **SDK clients (JS/Python)** below — the connect step is GUI either way.

## Watch it

<video src="../assets/screencast/08-social-post.mp4" controls width="100%"></video>

▶ If the video doesn't play inline, [open the screen recording](../assets/screencast/08-social-post.mp4) —
it walks through connecting YouTube and posting the movie in the web app.

## What the script does

1. `POST /workflow/fork-campaign` → a movie, then `export-render` it so there's a finished
   cut of **yours** to post (instant fork; one quick render).
2. **Ensure a connection** — `GET /social/connected-networks/{userId}`; if empty, it
   prints the dashboard link and polls until you've connected one.
   (`GET /social/network` lists the 9 networks you *can* connect.)
3. `POST /social/campaign-link { campaignId, connectedNetworkId }` → links the campaign to
   the network.
4. `POST /social/post-movie-batch/{movieId} { connectedNetworkIds: [...] }` → posts the
   rendered movie (the caption defaults to the movie's plot).
5. Poll `GET /social/post-status/{movieId}` until the network's latest `attempts[]` entry
   is `succeeded`, then print its `publishedUrl` (e.g. the YouTube link above).

## Run it

From `course/` (after Lesson 1):

```bash
bash 08-social-post/social-post.sh       # bash + curl
node 08-social-post/social-post.js       # JavaScript (yakyak-sdk)
python 08-social-post/social-post.py     # Python (yakyak-sdk)
```

If no network is connected yet, the script waits — connect one in the dashboard and it
continues automatically, ending with your published link.

## Notes

- **Post to several networks at once:** `post-movie-batch` takes a list —
  `connectedNetworkIds: [yt, ig, li]` — and `post-status` reports each one's attempts
  separately.
- **Auto-post:** a campaign link has an `autoPost` flag
  (`POST /social/update-campaign-link-autopost`) — turn it on and new renders of that
  campaign post themselves.
- **Posting is public and hard to undo.** Unlike the other lessons, this one has an
  outward-facing side effect (it publishes to a real account), so double-check the network
  before running it for real.
- **Manage connections:** `GET /social/connected-networks/{userId}` to list,
  `POST /social/disconnect-network` to remove one.
- Needs `yakyak-sdk` ≥ 0.0.7 (see the course [README](../README.md#2-prerequisite-sdk--007)).
