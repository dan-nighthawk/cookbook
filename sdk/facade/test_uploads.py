"""Unit tests for the Python `_Uploads` facade (sdk/facade/client.py).

Runs standalone (no pytest, no network): `python sdk/facade/test_uploads.py`.
The generated *Api imports inside YakYakClient are lazy, so this loads the module and
exercises `_Uploads` against a fake urllib3 transport.
"""
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("yk_facade_client", str(HERE / "client.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod._time.sleep = lambda *a, **k: None  # don't actually wait between retries

_Uploads = mod._Uploads


class FakeResp:
    def __init__(self, status, body):
        self.status = status
        self.data = body if isinstance(body, bytes) else json.dumps(body).encode()


class FakeHttp:
    """Records request() calls and returns queued responses."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, fields=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "fields": fields or {}})
        return self.responses.pop(0)


def up(responses, **kw):
    http = FakeHttp(responses)
    u = _Uploads(kw.get("base", "https://api.yakyak.ai/"), kw.get("token", "tok"),
                 kw.get("user_id"), http=http)
    return u, http


PASS = []


def check(name, cond):
    assert cond, "FAILED: " + name
    PASS.append(name)


# 1. cast_image: right URL, file tuple, default userId, campaignId, auth header, returns imageUrl
u, http = up([FakeResp(201, {"imageUrl": "https://cdn/x.png"})], user_id="user-1")
out = u.cast_image("camp-1", b"\x89PNG-bytes")
c = http.calls[0]
check("cast_image returns imageUrl", out == "https://cdn/x.png")
check("cast_image POST", c["method"] == "POST")
check("cast_image trailing-slash trimmed", c["url"] == "https://api.yakyak.ai/workflow/upload-cast-character-image")
check("cast_image auth header", c["headers"].get("Authorization") == "Bearer tok")
check("cast_image file field is (name,data,ct)", c["fields"]["file"] == ("upload", b"\x89PNG-bytes", "image/png"))
check("cast_image default userId from client", c["fields"]["userId"] == "user-1")
check("cast_image campaignId", c["fields"]["campaignId"] == "camp-1")

# 2. cast_image explicit user_id overrides the client default
u, http = up([FakeResp(201, {"imageUrl": "u"})], user_id="user-1")
u.cast_image("camp-2", b"x", user_id="override")
check("cast_image user_id override", http.calls[0]["fields"]["userId"] == "override")

# 3. scene_image: only sceneId, jpeg default, returns imageUrl
u, http = up([FakeResp(201, {"imageUrl": "img"})])
out = u.scene_image("scene-9", b"jpg")
check("scene_image returns imageUrl", out == "img")
check("scene_image url", http.calls[0]["url"].endswith("/workflow/upload-scene-image"))
check("scene_image fields", http.calls[0]["fields"]["sceneId"] == "scene-9" and http.calls[0]["fields"]["file"][2] == "image/jpeg")
check("scene_image no userId field", "userId" not in http.calls[0]["fields"])

# 4. user_media: returns the whole {id,url} object, sends filename both places
u, http = up([FakeResp(201, {"id": "m1", "url": "https://cdn/m.mp4"})], user_id="user-1")
out = u.user_media(b"vid", "opening.mp4")
check("user_media returns dict", out == {"id": "m1", "url": "https://cdn/m.mp4"})
check("user_media filename field", http.calls[0]["fields"]["filename"] == "opening.mp4")
check("user_media file name uses filename", http.calls[0]["fields"]["file"][0] == "opening.mp4")
check("user_media content-type", http.calls[0]["fields"]["file"][2] == "video/mp4")

# 5. soundtrack: movieId, returns audioPath
u, http = up([FakeResp(201, {"audioPath": "prd/.../a.mp3"})])
out = u.soundtrack("movie-7", b"mp3")
check("soundtrack returns audioPath", out == "prd/.../a.mp3")
check("soundtrack fields", http.calls[0]["fields"]["movieId"] == "movie-7" and http.calls[0]["fields"]["file"][2] == "audio/mpeg")

# 6. scene_movie (the one verified from the HAR): sceneId -> movieUrl
u, http = up([FakeResp(201, {"movieUrl": "https://cdn/s.mp4"})])
out = u.scene_movie("scene-2", b"mp4")
check("scene_movie returns movieUrl", out == "https://cdn/s.mp4")
check("scene_movie url", http.calls[0]["url"].endswith("/workflow/upload-scene-movie"))
check("scene_movie fields", http.calls[0]["fields"]["sceneId"] == "scene-2" and http.calls[0]["fields"]["file"][2] == "video/mp4")

# 7. retry on empty body, then success
u, http = up([FakeResp(200, b""), FakeResp(201, {"imageUrl": "after-retry"})])
out = u.scene_image("s", b"x")
check("retry returns after empty body", out == "after-retry")
check("retry made 2 calls", len(http.calls) == 2)

# 8. all-empty -> raises after 5 attempts
u, http = up([FakeResp(200, b"")] * 5)
try:
    u.scene_image("s", b"x")
    check("all-empty raises", False)
except RuntimeError:
    check("all-empty raises after 5 attempts", len(http.calls) == 5)

# 9. explicit filename + content_type override defaults
u, http = up([FakeResp(201, {"imageUrl": "img"})])
u.scene_image("s", b"x", filename="custom.webp", content_type="image/webp")
check("filename override", http.calls[0]["fields"]["file"][0] == "custom.webp")
check("content_type override", http.calls[0]["fields"]["file"][2] == "image/webp")

# 10. no token -> no Authorization header
u, http = up([FakeResp(201, {"imageUrl": "img"})], token=None)
u.scene_image("s", b"x")
check("no token -> no auth header", "Authorization" not in http.calls[0]["headers"])

print("\n".join("  ✓ " + n for n in PASS))
print(f"\nPython facade: {len(PASS)} checks passed")
sys.exit(0)
