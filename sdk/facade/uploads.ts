/* tslint:disable */
/* eslint-disable */
/**
 * Ergonomic wrappers over the `multipart/form-data` upload routes the generated client
 * can't express. Hand-maintained and copied into the generated package at publish time
 * (see .github/workflows/publish-sdks.yml). Kept free of generated-runtime imports so it
 * can be unit-tested in isolation. Written in erasable-only TS (no parameter properties)
 * so Node's type stripping can run it directly.
 */

/** A file payload for uploads: a Blob/File, or raw bytes. */
export type FileInput = Blob | Uint8Array | ArrayBuffer | ArrayBufferView;

export interface UploadOptions {
  /** The file to upload — a Blob/File or raw bytes. */
  file: FileInput;
  /** Filename to report in the multipart part (defaults per upload type). */
  filename?: string;
  /** MIME type of the file (defaults per upload type). */
  contentType?: string;
}

function toBlob(file: FileInput, contentType?: string): Blob {
  if (typeof Blob !== 'undefined' && file instanceof Blob) return file;
  return new Blob([file as BlobPart], contentType ? { type: contentType } : undefined);
}

/**
 * Each method builds the form, attaches Bearer auth, retries up to 5x on an empty body
 * (the endpoints occasionally return one), and returns the single useful field.
 */
export class Uploads {
  private readonly baseUrl: string;
  private readonly token: string | undefined;
  private readonly userId: string | undefined;

  constructor(baseUrl?: string, token?: string, userId?: string) {
    this.baseUrl = (baseUrl ?? '').replace(/\/$/, '');
    this.token = token;
    this.userId = userId;
  }

  private async post(
    path: string,
    fields: Record<string, string | undefined>,
    file: FileInput,
    filename: string,
    contentType: string,
    pick: (json: any) => any,
  ): Promise<any> {
    const url = this.baseUrl + path;
    const headers: Record<string, string> = {};
    if (this.token) headers['Authorization'] = 'Bearer ' + this.token;
    let lastErr: unknown;
    for (let attempt = 0; attempt < 5; attempt++) {
      try {
        const fd = new FormData();
        fd.append('file', toBlob(file, contentType), filename);
        for (const [k, v] of Object.entries(fields)) if (v != null) fd.append(k, v);
        const res = await fetch(url, { method: 'POST', headers, body: fd });
        if (res.ok) {
          const text = await res.text();
          if (text) {
            const picked = pick(JSON.parse(text));
            if (picked != null) return picked;
          }
        }
      } catch (e) {
        lastErr = e;
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
    throw new Error('upload to ' + path + ' failed after 5 attempts' + (lastErr ? ': ' + lastErr : ''));
  }

  /** Upload a custom cast character portrait. Returns the image URL. */
  castImage(o: UploadOptions & { campaignId: string; userId?: string }): Promise<string> {
    return this.post('/workflow/upload-cast-character-image',
      { userId: o.userId ?? this.userId, campaignId: o.campaignId },
      o.file, o.filename ?? 'image.png', o.contentType ?? 'image/png', (j) => j.imageUrl);
  }

  /** Upload a still image for a scene (bring-your-own image). Returns the image URL. */
  sceneImage(o: UploadOptions & { sceneId: string }): Promise<string> {
    return this.post('/workflow/upload-scene-image',
      { sceneId: o.sceneId },
      o.file, o.filename ?? 'image.jpg', o.contentType ?? 'image/jpeg', (j) => j.imageUrl);
  }

  /** Upload a pre-rendered video clip to the media library. Returns `{ id, url }`. */
  userMedia(o: UploadOptions & { filename: string; userId?: string }): Promise<{ id: string; url: string }> {
    return this.post('/workflow/upload-user-media',
      { userId: o.userId ?? this.userId, filename: o.filename },
      o.file, o.filename, o.contentType ?? 'video/mp4', (j) => (j && j.url != null ? j : null));
  }

  /** Upload a soundtrack audio file. Returns the audio path. */
  soundtrack(o: UploadOptions & { movieId: string }): Promise<string> {
    return this.post('/workflow/upload-soundtrack-audio',
      { movieId: o.movieId },
      o.file, o.filename ?? 'audio.mp3', o.contentType ?? 'audio/mpeg', (j) => j.audioPath);
  }

  /** Upload a pre-rendered movie for a scene (subtitles get burned on top). Returns the movie URL. */
  sceneMovie(o: UploadOptions & { sceneId: string }): Promise<string> {
    return this.post('/workflow/upload-scene-movie',
      { sceneId: o.sceneId },
      o.file, o.filename ?? 'movie.mp4', o.contentType ?? 'video/mp4', (j) => j.movieUrl);
  }
}
