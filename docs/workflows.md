# Workflows & use cases

The end-to-end flow a user moves through in YakYak — from one of four entry points,
through authoring (cast + scenes), to soundtrack, render, and distribution.

Stages and routes below are taken from the API
(`WorkflowController` @ `workflow`, `SocialController` @ `social`); paths are served
at the **root**, e.g. `POST https://api.yakyak.ai/workflow/create-campaign`. Only the
interactive docs live under `/api` (Swagger UI at `/api/docs`).

```mermaid
flowchart TB
    classDef entry fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20;
    classDef edit  fill:#e3f2fd,stroke:#1565c0,color:#0d47a1;
    classDef out   fill:#fff3e0,stroke:#e65100,color:#bf360c;
    classDef human fill:#fafafa,stroke:#9e9e9e,color:#424242;

    %% ---------- Start: four user-initiated entry points ----------
    subgraph START["Start — user-initiated"]
      direction LR
      FMG["👤 Fork movie from grid<br/><small>fork-campaign · sourceMovieId<br/>(only the single movie)</small>"]:::entry
      FC["👤 Fork campaign<br/><small>fork-campaign · whole campaign</small>"]:::entry
      NC["👤 New campaign<br/><small>create-campaign</small>"]:::entry
      IC["👤 Import campaign<br/><small>import-campaign</small>"]:::entry
    end

    %% ---------- Authoring ----------
    subgraph CAST["Edit cast"]
      direction LR
      AIC["AI cast<br/><small>gen-movie-cast</small>"]:::edit
      CC["Custom cast<br/><small>save-movie-custom-cast</small>"]:::edit
    end
    ED["Edit<br/><small>update-campaign-settings · movie editor</small>"]:::edit
    ES["Edit scene<br/><small>create-scene · update-scene-* · regen-scene-asset</small>"]:::edit

    NC --> CAST
    IC --> ED
    FMG --> ES
    FC --> ES
    CAST <--> ES
    ED --> ES

    %% ---------- Soundtrack, render, distribute ----------
    ST["Soundtrack — pick existing<br/><small>available-soundtracks · select-soundtrack-history</small>"]:::edit
    GM["Generate new music<br/><small>gen-movie-soundtrack</small>"]:::edit
    PR["Preview / Render<br/><small>export-render → scene-concat + soundtrack · render-movie</small>"]:::out
    DL["👤 Download<br/><small>preview-movie → S3 URL</small>"]:::human
    PUB["Publish to social network<br/><small>social/post-movie-batch</small>"]:::out
    AUD["👥 Audience<br/><small>connected networks</small>"]:::human

    ES -->|EXPORT<br/>export-render| ST
    ST <-->|generate or pick| GM
    ST --> PR
    PR --> DL
    PR --> PUB
    PUB --> AUD
```

## Stages → API routes

All `workflow/*` routes are on `WorkflowController`; `social/*` on `SocialController`.

### Entry points

| Stage | Route | Notes |
|-------|-------|-------|
| **Fork movie from grid** | `POST /workflow/fork-campaign` | Pass `sourceMovieId` → forks **only that single movie**. |
| **Fork campaign** | `POST /workflow/fork-campaign` | Omit `sourceMovieId` → deep-copies the **whole campaign**. |
| **New campaign** | `POST /workflow/create-campaign` | Then `gen-movie-summary` → cast. |
| **Import campaign** | `POST /workflow/import-campaign` | Consumes JSON from `GET /workflow/export-campaign/:campaignId`. |

### Authoring

| Stage | Route(s) |
|-------|----------|
| **Edit cast → AI cast** | `POST /workflow/gen-movie-cast` (+ `gen-movie-cast-image`, `-voice`, `-subtitle`) |
| **Edit cast → Custom cast** | `POST /workflow/save-movie-custom-cast` (+ `upload-cast-character-image`, `cast-image-history`, `select-cast-image`) |
| **Edit** (import landing) | `POST /workflow/update-campaign-settings`, `switch-campaign-mode`, movie-level `update-movie-*` |
| **Edit scene** (hub) | `create-scene`, `delete-scene`, `reorder-scenes`, `update-scene-dialogue / -title / -story / -lead-cast / -animation-prompt / -background-color`, `regen-scene-asset`, `select-scene-asset`, `get-scene-progress/:sceneId` |

`Edit cast ⇄ Edit scene` is iterative — you can move back and forth while authoring.

### Soundtrack · render · distribute

| Stage | Route(s) |
|-------|----------|
| **Export** (Scene → Soundtrack) | `POST /workflow/export-render` — change-aware; triggers `gen-movie-scene-concat` then soundtrack |
| **Soundtrack — pick existing** | `GET /workflow/available-soundtracks/:movieId`, `POST /workflow/select-soundtrack-history` |
| **Generate new music** | `POST /workflow/gen-movie-soundtrack` (+ `suggested-music-prompt`, `soundtrack-history`, `set-soundtrack`) |
| **Preview / Render** | `POST /workflow/render-movie` (full) / `export-render` (smart); `GET /workflow/get-movie-progress/:movieId` |
| **Download** | `GET /workflow/preview-movie/:movieId` returns the movie's S3 URL (public for published movies); no dedicated file endpoint |
| **Publish to social network** | `POST /social/post-movie-batch/:movieId` (or `post-movie/:movieId/:connectedNetworkId`); status via `GET /social/post-status/:movieId` |

Publishing presupposes connected networks: `POST /social/connect-network`,
`POST /social/campaign-link`, and per-campaign auto-post
(`PATCH /social/campaign-link/:campaignId/:connectedNetworkId/auto-post`).

> Transcribed from a design sketch and cross-checked against the API controllers.
> See the [model overview](README.md) for the campaign → movie → scene → cast
> objects and the full `gen-*` generation pipeline.
