"""Load Bilibili-only browser cookies without exposing them to other hosts."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlsplit


JSON_COOKIE_PATH = Path("data/bilibili-cookies.json")
NETSCAPE_COOKIE_PATH = Path("data/cookies.txt")


class BiliCookieError(ValueError):
    """The supplied cookie file is invalid or belongs to another site."""


def _bilibili_domain(domain: str) -> bool:
    host = domain.lstrip(".").lower()
    return host == "bilibili.com" or host.endswith(".bilibili.com")


def _validate_domain(domain: str) -> str:
    if not isinstance(domain, str) or not domain or not _bilibili_domain(domain):
        site = str(domain).lstrip(".").lower()
        if site == "chatgpt.com" or site.endswith(".chatgpt.com"):
            raise BiliCookieError("提供的是 ChatGPT Cookie；此项目需要 bilibili.com 的 Cookie")
        raise BiliCookieError(f"Cookie 域名不是 B站：{site}")
    return domain.lower()


def _validate_cookie(name: str, value: str) -> None:
    if not isinstance(name, str) or not name or any(c in name for c in ";=\r\n\t"):
        raise BiliCookieError("Cookie 名称无效")
    if not isinstance(value, str) or any(c in value for c in "\r\n"):
        raise BiliCookieError("Cookie 值无效")


def _from_json(path: Path) -> list[dict]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise BiliCookieError(f"无法读取 B站 JSON Cookie：{path}") from exc
    if isinstance(payload, dict):
        payload = payload.get("cookies")
    if not isinstance(payload, list):
        raise BiliCookieError("B站 JSON Cookie 应为列表或包含 cookies 列表的对象")
    cookies = []
    for raw in payload:
        if not isinstance(raw, dict):
            raise BiliCookieError("B站 JSON Cookie 中有无效条目")
        domain = _validate_domain(raw.get("domain"))
        name, value = raw.get("name"), raw.get("value")
        _validate_cookie(name, value)
        cookie = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": raw.get("path") or "/",
            "secure": bool(raw.get("secure", False)),
            "httpOnly": bool(raw.get("httpOnly", False)),
        }
        expires = raw.get("expirationDate", raw.get("expires"))
        if expires is not None:
            try:
                expires = float(expires)
            except (TypeError, ValueError) as exc:
                raise BiliCookieError("B站 JSON Cookie 的过期时间无效") from exc
            if expires > 0:
                cookie["expires"] = expires
        same_site = str(raw.get("sameSite") or "").lower()
        if same_site in ("lax", "strict", "none", "no_restriction"):
            cookie["sameSite"] = {
                "lax": "Lax", "strict": "Strict", "none": "None",
                "no_restriction": "None",
            }[same_site]
        cookies.append(cookie)
    return cookies


def _from_netscape(path: Path) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise BiliCookieError(f"无法读取 B站 Netscape Cookie：{path}") from exc
    cookies = []
    for line in lines:
        if not line.strip() or (line.startswith("#") and not line.startswith("#HttpOnly_")):
            continue
        fields = line.split("\t")
        if len(fields) != 7:
            raise BiliCookieError("Netscape Cookie 文件包含无效行")
        domain, include_subdomains, cookie_path, secure, expires, name, value = fields
        http_only = domain.startswith("#HttpOnly_")
        if http_only:
            domain = domain.removeprefix("#HttpOnly_")
        domain = _validate_domain(domain)
        _validate_cookie(name, value)
        if include_subdomains.upper() == "TRUE" and not domain.startswith("."):
            domain = "." + domain
        try:
            expires_at = float(expires)
        except ValueError as exc:
            raise BiliCookieError("Netscape Cookie 的过期时间无效") from exc
        cookie = {
            "name": name, "value": value, "domain": domain,
            "path": cookie_path or "/", "secure": secure.upper() == "TRUE",
            "httpOnly": http_only,
        }
        if expires_at > 0:
            cookie["expires"] = expires_at
        cookies.append(cookie)
    return cookies


def load_bilibili_cookies(path: Path | None = None) -> list[dict]:
    """Read Chrome-export JSON or Netscape cookies; reject all other domains."""
    if path is None:
        if JSON_COOKIE_PATH.exists():
            path = JSON_COOKIE_PATH
        elif NETSCAPE_COOKIE_PATH.exists():
            path = NETSCAPE_COOKIE_PATH
        else:
            return []
    path = Path(path)
    if path.suffix.lower() == ".json":
        return _from_json(path)
    return _from_netscape(path)


def cookie_header(url: str, cookies: list[dict] | None = None) -> str:
    """Build an HTTP Cookie header only for HTTPS Bilibili URLs."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not _bilibili_domain(host):
        raise BiliCookieError("禁止向非 HTTPS B站地址发送 Cookie")
    if cookies is None:
        cookies = load_bilibili_cookies()
    path = parsed.path or "/"
    now = time.time()
    selected = []
    for cookie in cookies:
        domain = _validate_domain(cookie["domain"])
        if domain.startswith("."):
            matches = host == domain[1:] or host.endswith(domain)
        else:
            matches = host == domain
        cookie_path = cookie.get("path") or "/"
        path_matches = path == cookie_path or path.startswith(cookie_path.rstrip("/") + "/")
        if (matches and path_matches and
                (not cookie.get("secure") or parsed.scheme == "https") and
                (not cookie.get("expires") or float(cookie["expires"]) > now)):
            _validate_cookie(cookie["name"], cookie["value"])
            selected.append(f"{cookie['name']}={cookie['value']}")
    return "; ".join(selected)
