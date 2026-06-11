/* tslint:disable */
/* eslint-disable */
/**
 * Unit tests for the JS `Uploads` facade (sdk/facade/uploads.ts).
 * Runs standalone on Node >= 22.6 (type stripping): `node sdk/facade/uploads.test.ts`.
 * No network: global `fetch` is mocked and `setTimeout` is made instant.
 */
import { Uploads } from './uploads.ts';

const realFetch = globalThis.fetch;
const realSetTimeout = globalThis.setTimeout;
// Make retry backoff instant.
(globalThis as any).setTimeout = (fn: any) => { fn(); return 0 as any; };

type Call = { url: string; opts: any };

function mockFetch(responses: Array<{ ok?: boolean; body: string }>) {
  const calls: Call[] = [];
  let i = 0;
  (globalThis as any).fetch = async (url: string, opts: any) => {
    calls.push({ url, opts });
    const r = responses[Math.min(i++, responses.length - 1)];
    return { ok: r.ok !== false, text: async () => r.body } as any;
  };
  return calls;
}

const passed: string[] = [];
function check(name: string, cond: boolean) {
  if (!cond) throw new Error('FAILED: ' + name);
  passed.push(name);
}
const jsonResp = (o: any) => ({ body: JSON.stringify(o) });

async function main() {
  // 1. castImage: URL (trailing slash trimmed), file + default userId + campaignId, auth, returns imageUrl
  let calls = mockFetch([jsonResp({ imageUrl: 'https://cdn/x.png' })]);
  let u = new Uploads('https://api.yakyak.ai/', 'tok', 'user-1');
  let out = await u.castImage({ campaignId: 'camp-1', file: new Uint8Array([1, 2, 3]) });
  check('castImage returns imageUrl', out === 'https://cdn/x.png');
  check('castImage url trimmed', calls[0].url === 'https://api.yakyak.ai/workflow/upload-cast-character-image');
  check('castImage POST', calls[0].opts.method === 'POST');
  check('castImage auth header', calls[0].opts.headers['Authorization'] === 'Bearer tok');
  let fd = calls[0].opts.body as FormData;
  check('castImage default userId', fd.get('userId') === 'user-1');
  check('castImage campaignId', fd.get('campaignId') === 'camp-1');
  check('castImage file is a Blob', (fd.get('file') as Blob)?.size === 3);
  check('castImage file content-type', (fd.get('file') as Blob)?.type === 'image/png');

  // 2. explicit userId overrides default
  calls = mockFetch([jsonResp({ imageUrl: 'u' })]);
  u = new Uploads('https://b', 'tok', 'user-1');
  await u.castImage({ campaignId: 'c', file: new Uint8Array([0]), userId: 'override' });
  check('castImage userId override', (calls[0].opts.body as FormData).get('userId') === 'override');

  // 3. sceneImage: sceneId only, no userId, returns imageUrl
  calls = mockFetch([jsonResp({ imageUrl: 'img' })]);
  u = new Uploads('https://b', 'tok');
  out = await u.sceneImage({ sceneId: 'scene-9', file: new Uint8Array([1]) });
  check('sceneImage returns imageUrl', out === 'img');
  check('sceneImage url', calls[0].url.endsWith('/workflow/upload-scene-image'));
  fd = calls[0].opts.body as FormData;
  check('sceneImage sceneId', fd.get('sceneId') === 'scene-9');
  check('sceneImage no userId', fd.get('userId') === null);

  // 4. userMedia: returns whole { id, url }, filename in field + file name
  calls = mockFetch([jsonResp({ id: 'm1', url: 'https://cdn/m.mp4' })]);
  u = new Uploads('https://b', 'tok', 'user-1');
  const media = await u.userMedia({ file: new Uint8Array([1, 2]), filename: 'opening.mp4' });
  check('userMedia returns object', media.id === 'm1' && media.url === 'https://cdn/m.mp4');
  fd = calls[0].opts.body as FormData;
  check('userMedia filename field', fd.get('filename') === 'opening.mp4');
  check('userMedia file content-type', (fd.get('file') as Blob)?.type === 'video/mp4');

  // 5. soundtrack -> audioPath
  calls = mockFetch([jsonResp({ audioPath: 'prd/a.mp3' })]);
  u = new Uploads('https://b', 'tok');
  out = await u.soundtrack({ movieId: 'movie-7', file: new Uint8Array([1]) });
  check('soundtrack returns audioPath', out === 'prd/a.mp3');
  check('soundtrack movieId', (calls[0].opts.body as FormData).get('movieId') === 'movie-7');

  // 6. sceneMovie (HAR-verified) -> movieUrl
  calls = mockFetch([jsonResp({ movieUrl: 'https://cdn/s.mp4' })]);
  u = new Uploads('https://b', 'tok');
  out = await u.sceneMovie({ sceneId: 'scene-2', file: new Uint8Array([1]) });
  check('sceneMovie returns movieUrl', out === 'https://cdn/s.mp4');
  check('sceneMovie url', calls[0].url.endsWith('/workflow/upload-scene-movie'));
  check('sceneMovie sceneId', (calls[0].opts.body as FormData).get('sceneId') === 'scene-2');

  // 7. retry on empty body then success
  calls = mockFetch([{ body: '' }, jsonResp({ imageUrl: 'after-retry' })]);
  u = new Uploads('https://b', 'tok');
  out = await u.sceneImage({ sceneId: 's', file: new Uint8Array([1]) });
  check('retry returns after empty body', out === 'after-retry');
  check('retry made 2 calls', calls.length === 2);

  // 8. all-empty -> rejects after 5 attempts
  calls = mockFetch([{ body: '' }, { body: '' }, { body: '' }, { body: '' }, { body: '' }]);
  u = new Uploads('https://b', 'tok');
  let threw = false;
  try { await u.sceneImage({ sceneId: 's', file: new Uint8Array([1]) }); }
  catch { threw = true; }
  check('all-empty rejects', threw);
  check('all-empty tried 5 times', calls.length === 5);

  // 9. !res.ok is treated as a failure (retried)
  calls = mockFetch([{ ok: false, body: 'err' }, jsonResp({ imageUrl: 'ok' })]);
  u = new Uploads('https://b', 'tok');
  out = await u.sceneImage({ sceneId: 's', file: new Uint8Array([1]) });
  check('non-ok response retried', out === 'ok' && calls.length === 2);

  // 10. no token -> no Authorization header
  calls = mockFetch([jsonResp({ imageUrl: 'img' })]);
  u = new Uploads('https://b');
  await u.sceneImage({ sceneId: 's', file: new Uint8Array([1]) });
  check('no token -> no auth header', !('Authorization' in calls[0].opts.headers));

  // 11. accepts a Blob directly (passes through)
  calls = mockFetch([jsonResp({ imageUrl: 'img' })]);
  u = new Uploads('https://b', 'tok');
  await u.castImage({ campaignId: 'c', file: new Blob([new Uint8Array([9, 9])], { type: 'image/png' }) });
  check('accepts Blob input', (calls[0].opts.body as FormData).get('file') instanceof Blob);
}

main()
  .then(() => {
    globalThis.fetch = realFetch;
    globalThis.setTimeout = realSetTimeout;
    console.log(passed.map((n) => '  ✓ ' + n).join('\n'));
    console.log(`\nJS facade: ${passed.length} checks passed`);
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
