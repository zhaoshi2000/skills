"""Small, read-only client for public Bilibili video metadata and comments."""

from __future__ import annotations

import hashlib
import json
import time
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .cookies import cookie_header


API_ROOT = "https://api.bilibili.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_MIXIN_KEY_TABLE = (
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27,
    43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48,
    7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54,
    21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
)
_wbi_key: str | None = None
_wbi_key_time = 0.0


class BiliAPIError(RuntimeError):
    """Bilibili did not return the requested public data."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        # A Cookie header must never be forwarded to a redirect target.
        raise BiliAPIError(f"B站接口意外跳转：{code}")


def _get_json(path: str, params: dict | None = None, allowed_codes=(0,)) -> dict:
    url = API_ROOT + path
    if params:
        url += "?" + urlencode(params)
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json",
    }
    auth = cookie_header(url)
    if auth:
        headers["Cookie"] = auth
    request = Request(url, headers=headers)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=15) as response:
            payload = json.load(response)
    except (OSError, ValueError) as exc:
        raise BiliAPIError(f"B站接口请求失败：{path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("code") not in allowed_codes:
        code = payload.get("code") if isinstance(payload, dict) else "unknown"
        message = payload.get("message") if isinstance(payload, dict) else "invalid JSON"
        raise BiliAPIError(f"B站接口返回错误：{path}: {code} {message}")
    return payload.get("data") or {}


def fetch_video_meta(bvid: str) -> dict:
    """Return title, description, duration, aid and first-part cid for a BV video."""
    data = _get_json("/x/web-interface/view", {"bvid": bvid})
    if not data.get("aid") or not data.get("cid"):
        raise BiliAPIError(f"B站视频缺少 aid/cid：{bvid}")
    return {
        "title": data.get("title") or "",
        "description": data.get("desc") or "",
        "duration": data.get("duration") or 0,
        "aid": data["aid"],
        "cid": data["cid"],
    }


def _get_wbi_key() -> str:
    global _wbi_key, _wbi_key_time
    if _wbi_key and time.time() - _wbi_key_time < 3600:
        return _wbi_key
    # Anonymous nav responses use -101 but still include the public WBI images.
    data = _get_json("/x/web-interface/nav", allowed_codes=(0, -101))
    images = data.get("wbi_img") or {}
    lookup = "".join(
        str(images.get(name) or "").rpartition("/")[2].partition(".")[0]
        for name in ("img_url", "sub_url")
    )
    if len(lookup) < 64:
        raise BiliAPIError("B站没有返回有效的 WBI 签名图片")
    _wbi_key = "".join(lookup[index] for index in _MIXIN_KEY_TABLE)[:32]
    _wbi_key_time = time.time()
    return _wbi_key


def _sign_wbi(params: dict) -> dict:
    values = {**params, "wts": int(time.time())}
    cleaned = {
        key: "".join(char for char in str(value) if char not in "!'()*")
        for key, value in sorted(values.items())
    }
    query = urlencode(cleaned)
    cleaned["w_rid"] = hashlib.md5((query + _get_wbi_key()).encode()).hexdigest()
    return cleaned


def fetch_comments(aid: int, limit: int = 30) -> dict:
    """Return at most `limit` top-level comments, with sampled and reported totals."""
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    comments = []
    next_cursor = 0
    total = None
    while len(comments) < limit:
        data = _get_json(
            "/x/v2/reply/wbi/main",
            _sign_wbi({
                "type": 1,
                "oid": aid,
                "mode": 3,  # hot comments
                "next": next_cursor,
                "ps": min(20, limit - len(comments)),
                "web_location": 1315875,
            }),
        )
        cursor = data.get("cursor") or {}
        if total is None:
            total = cursor.get("all_count")
        replies = data.get("replies") or []
        for reply in replies:
            message = (reply.get("content") or {}).get("message") or ""
            if message.strip():
                content = message.strip()[:500]
                if any(existing["content"] == content for existing in comments):
                    continue
                comments.append({
                    "content": content,
                    "likes": reply.get("like") or 0,
                    "reply_count": reply.get("rcount") or 0,
                })
                if len(comments) >= limit:
                    break
        new_cursor = cursor.get("next")
        if not replies or cursor.get("is_end") or new_cursor is None or new_cursor == next_cursor:
            break
        next_cursor = new_cursor
    return {"comments": comments, "count": len(comments), "total": total}
