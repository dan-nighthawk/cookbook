"""Ergonomic client facade over the generated yakyak_sdk output.

Hand-maintained and copied into the generated package at publish time (see
.github/workflows/publish-sdks.yml). Provides a single `YakYakClient` that exposes the
raw generated `*Api` classes under friendly namespaces (`client.workflow`, `client.data`,
…) plus `client.uploads.*` helpers that hide the `multipart/form-data` upload routes the
generator can't express.
"""
import json as _json
import os as _os
import time as _time

import urllib3 as _urllib3

_RETRIES = 5
_RETRY_DELAY = 2.0


def _read_file(file, filename):
    """Normalize a path str / bytes / file-like into (filename, data)."""
    if isinstance(file, (bytes, bytearray)):
        return (filename or "upload"), bytes(file)
    if hasattr(file, "read"):
        data = file.read()
        name = filename or _os.path.basename(getattr(file, "name", "") or "") or "upload"
        return name, data
    with open(file, "rb") as fh:
        data = fh.read()
    return (filename or _os.path.basename(_os.fspath(file))), data


class _Uploads:
    """Multipart upload helpers. Each builds the form, attaches Bearer auth, retries up
    to 5x on an empty body (the endpoints occasionally return one), and returns the single
    useful field from the JSON response.
    """

    def __init__(self, base_url, token, user_id=None, http=None):
        self._base = (base_url or "").rstrip("/")
        self._token = token
        self._user_id = user_id
        self._http = http or _urllib3.PoolManager()

    def _post(self, path, fields, file, filename, content_type, pick):
        url = self._base + path
        headers = {}
        if self._token:
            headers["Authorization"] = "Bearer " + self._token
        name, data = _read_file(file, filename)
        form = {k: v for k, v in fields.items() if v is not None}
        form["file"] = (name, data, content_type)
        last = None
        for _ in range(_RETRIES):
            try:
                resp = self._http.request("POST", url, headers=headers, fields=form)
                if resp.status < 300 and resp.data:
                    picked = pick(_json.loads(resp.data.decode("utf-8")))
                    if picked is not None:
                        return picked
            except Exception as e:  # noqa: BLE001 — retry on any transport/parse error
                last = e
            _time.sleep(_RETRY_DELAY)
        raise RuntimeError("upload to %s failed after %d attempts%s"
                           % (path, _RETRIES, (": %s" % last) if last else ""))

    def cast_image(self, campaign_id, file, user_id=None, filename=None, content_type="image/png"):
        """Upload a custom cast character portrait. Returns the image URL."""
        return self._post("/workflow/upload-cast-character-image",
                          {"userId": user_id or self._user_id, "campaignId": campaign_id},
                          file, filename, content_type, lambda j: j.get("imageUrl"))

    def scene_image(self, scene_id, file, filename=None, content_type="image/jpeg"):
        """Upload a still image for a scene (bring-your-own image). Returns the image URL."""
        return self._post("/workflow/upload-scene-image",
                          {"sceneId": scene_id},
                          file, filename, content_type, lambda j: j.get("imageUrl"))

    def user_media(self, file, filename, user_id=None, content_type="video/mp4"):
        """Upload a pre-rendered video clip to the media library. Returns ``{id, url}``."""
        return self._post("/workflow/upload-user-media",
                          {"userId": user_id or self._user_id, "filename": filename},
                          file, filename, content_type, lambda j: j if j.get("url") else None)

    def soundtrack(self, movie_id, file, filename=None, content_type="audio/mpeg"):
        """Upload a soundtrack audio file. Returns the audio path."""
        return self._post("/workflow/upload-soundtrack-audio",
                          {"movieId": movie_id},
                          file, filename, content_type, lambda j: j.get("audioPath"))

    def scene_movie(self, scene_id, file, filename=None, content_type="video/mp4"):
        """Upload a pre-rendered movie for a scene (subtitles get burned on top). Returns the movie URL."""
        return self._post("/workflow/upload-scene-movie",
                          {"sceneId": scene_id},
                          file, filename, content_type, lambda j: j.get("movieUrl"))


class YakYakClient:
    """Unified entry point: raw API namespaces plus ergonomic ``uploads``.

    Example::

        yak = YakYakClient(base_url="https://api.yakyak.ai", token=TOKEN, user_id=USER)
        yak.workflow.workflow_controller_create_campaign(...)   # raw generated calls
        url = yak.uploads.cast_image(campaign_id, "hero.png")   # multipart, hidden
    """

    def __init__(self, base_url=None, token=None, user_id=None, **kwargs):
        # Imported lazily so this module (and _Uploads) can be imported standalone.
        from .api.data_api import DataApi
        from .api.scheduler_api import SchedulerApi
        from .api.social_api import SocialApi
        from .api.users_api import UsersApi
        from .api.workflow_api import WorkflowApi
        from .api_client import ApiClient
        from .configuration import Configuration

        self.config = Configuration(host=base_url, access_token=token, **kwargs)
        self.api_client = ApiClient(self.config)
        self.workflow = WorkflowApi(self.api_client)
        self.data = DataApi(self.api_client)
        self.social = SocialApi(self.api_client)
        self.users = UsersApi(self.api_client)
        self.scheduler = SchedulerApi(self.api_client)
        self.uploads = _Uploads(base_url, token, user_id)
