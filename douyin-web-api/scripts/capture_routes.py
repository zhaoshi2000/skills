"""Navigation-only Douyin network inventory. Stores no credential values."""
import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def load_cookies(cookie_file: Path):
    raw = json.loads(cookie_file.read_text(encoding="utf-8-sig"))
    result = []
    for item in raw:
        domain = item.get("domain", "").lower()
        if domain not in {".douyin.com", "douyin.com", "www.douyin.com"} or not item.get("name"):
            continue
        expires = item.get("expirationDate")
        if expires and float(expires) <= time.time():
            continue
        cookie = {"name": item["name"], "value": item["value"], "domain": domain,
                  "path": item.get("path", "/"), "secure": bool(item.get("secure", False)),
                  "httpOnly": bool(item.get("httpOnly", False))}
        same = item.get("sameSite")
        if same == "no_restriction":
            same = "None"
        if same in {"Lax", "Strict", "None"}:
            cookie["sameSite"] = same
        if expires and float(expires) > time.time():
            cookie["expires"] = float(expires)
        result.append(cookie)
    return result

def body_keys(req):
    if req.method in {"GET", "HEAD"}:
        return []
    body = req.post_data or ""
    if not body:
        return []
    ctype = req.headers.get("content-type", "")
    if "application/json" in ctype:
        try:
            obj = json.loads(body)
            return sorted(obj) if isinstance(obj, dict) else ["<array>"]
        except Exception:
            return ["<json-parse-error>"]
    if "application/x-www-form-urlencoded" in ctype:
        return sorted(parse_qs(body))
    if "multipart/form-data" in ctype:
        return sorted(set(re.findall(r'name="([^"\r\n]+)"', body)))
    return ["<opaque-body>"]

def safe_path(value: str) -> str:
    value = re.sub(r"^/(video|note)/[^/]+", r"/\1/<id>", value)
    if value.startswith("/user/") and not value.startswith("/user/self"):
        value = re.sub(r"^/user/[^/]+", "/user/<id>", value)
    value = re.sub(r"/[0-9]{12,}(?=/|$)", "/<id>", value)
    return re.sub(r"/MS4[A-Za-z0-9_-]{12,}(?=/|$)", "/<id>", value)

def is_douyin_link(value: str, prefix: str) -> bool:
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and parsed.hostname in {"douyin.com", "www.douyin.com"}
                and not parsed.username and not parsed.password and parsed.port in {None, 443}
                and parsed.path.startswith(prefix))
    except ValueError:
        return False

def first_value(obj, key):
    """Read a navigation ID in memory; never persist it in the network inventory."""
    if isinstance(obj, dict):
        if key in obj and obj[key]:
            return obj[key]
        for value in obj.values():
            found = first_value(value, key)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj[:30]:
            found = first_value(value, key)
            if found:
                return found
    return None

def first_video_id(obj):
    if isinstance(obj, dict):
        candidate = obj.get("aweme_id")
        if candidate and str(candidate).isdigit() and len(str(candidate)) >= 12:
            if obj.get("aweme_type") == 0 and isinstance(obj.get("video"), dict):
                return str(candidate)
        for value in obj.values():
            found = first_video_id(value)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj[:50]:
            found = first_video_id(value)
            if found:
                return found
    return None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cookies", type=Path, required=True,
                        help="浏览器导出的抖音 Cookie JSON；仅在本机读取")
    parser.add_argument("--output-dir", type=Path, default=Path("data/capture"),
                        help="脱敏路由清单保存位置")
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "douyin_network.json"
    pages_file = output_dir / "douyin_pages.json"
    records = {}
    pages = []
    observed_ids = {"video": None, "user": None}
    login_proven = False
    with sync_playwright() as pw:
        launch_options = {"headless": True,
                          "args": ["--disable-blink-features=AutomationControlled"]}
        try:
            browser = pw.chromium.launch(channel="chrome", **launch_options)
        except Exception:
            browser = pw.chromium.launch(**launch_options)
        ctx = browser.new_context(locale="zh-CN", timezone_id="Asia/Shanghai",
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
        ctx.add_cookies(load_cookies(args.cookies.expanduser().resolve()))
        page = ctx.new_page()
        current_page = "startup"
        def on_request(req):
            if req.resource_type not in {"xhr", "fetch"}:
                return
            parsed = urlsplit(req.url)
            host = (parsed.hostname or "").lower()
            if not (host.endswith("douyin.com") or host.endswith("amemv.com") or host.endswith("bytedance.net") or host.endswith("snssdk.com")):
                return
            records[req] = {"page": current_page, "host": host, "method": req.method,
                            "path": safe_path(parsed.path), "query_keys": sorted(parse_qs(parsed.query)),
                            "body_keys": body_keys(req), "status": None, "business_code": None}
        def on_response(resp):
            nonlocal login_proven
            record = records.get(resp.request)
            if record:
                record["status"] = resp.status
                if "json" in resp.headers.get("content-type", ""):
                    try:
                        payload = resp.json()
                        if isinstance(payload, dict):
                            code = payload.get("status_code", payload.get("code"))
                            if isinstance(code, (int, str)) and len(str(code)) <= 12:
                                record["business_code"] = code
                            if resp.url.startswith("https://www.douyin.com/aweme/v1/web/user/profile/self/") and code == 0:
                                login_proven = True
                            if any(x in record["path"] for x in ("/follow/feed/", "/aweme/favorite/", "/module/feed/", "/aweme/post/")):
                                aweme = first_video_id(payload)
                                user = first_value(payload, "sec_uid")
                                if aweme:
                                    observed_ids["video"] = aweme
                                if user and isinstance(user, str) and len(user) > 12:
                                    observed_ids["user"] = user
                    except Exception:
                        pass
        ctx.on("request", on_request)
        ctx.on("response", on_response)

        targets = [
            ("home", "https://www.douyin.com/"),
            ("search", "https://www.douyin.com/search/%E7%A7%91%E6%8A%80?type=general"),
        ]
        i = 0
        while i < len(targets):
            label, url = targets[i]
            current_page = label
            result = {"label": label, "requested_host": urlsplit(url).hostname,
                      "requested_path": safe_path(urlsplit(url).path), "error": None}
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(6500)
                parsed = urlsplit(page.url)
                result.update({"final_host": parsed.hostname, "final_path": safe_path(parsed.path),
                               "captcha_page": "验证码" in page.title()})
                if label == "home":
                    links = page.locator('a[href]').evaluate_all("els => els.map(x=>x.href)")
                    video = next((x for x in links if is_douyin_link(x, "/video/")), None)
                    user = next((x for x in links if is_douyin_link(x, "/user/") and "/user/self" not in x), None)
                    if video:
                        targets += [("video", video)]
                    if user:
                        targets += [("user", user)]
                    result["video_link_found"] = bool(video)
                    result["user_link_found"] = bool(user)
            except Exception as exc:
                result["error"] = type(exc).__name__
            pages.append(result)
            i += 1
        for label, url in [
            ("follow", "https://www.douyin.com/follow"),
            ("favorites", "https://www.douyin.com/user/self?showTab=favorite_collection"),
            ("messages", "https://www.douyin.com/message"),
            ("live", "https://live.douyin.com/"),
            ("creator", "https://creator.douyin.com/creator-micro/home"),
            ("creator_upload", "https://creator.douyin.com/creator-micro/content/upload"),
            ("self_posts", "https://www.douyin.com/user/self?showTab=post"),
            ("self_likes", "https://www.douyin.com/user/self?showTab=like"),
            ("self_collection", "https://www.douyin.com/user/self?showTab=collection"),
            ("discover", "https://www.douyin.com/discover"),
            ("hot", "https://www.douyin.com/hot"),
            ("creator_manage", "https://creator.douyin.com/creator-micro/content/manage"),
            ("creator_data", "https://creator.douyin.com/creator-micro/data/overview"),
        ]:
            current_page = label
            result = {"label": label, "requested_host": urlsplit(url).hostname,
                      "requested_path": safe_path(urlsplit(url).path), "error": None}
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4500)
                parsed = urlsplit(page.url)
                result.update({"final_host": parsed.hostname, "final_path": safe_path(parsed.path),
                               "captcha_page": "验证码" in page.title()})
            except Exception as exc:
                result["error"] = type(exc).__name__
            pages.append(result)
        for label in ("user", "video"):
            url = (f"https://www.douyin.com/video/{observed_ids['video']}" if label == "video" and observed_ids["video"]
                   else f"https://www.douyin.com/user/{observed_ids['user']}" if label == "user" and observed_ids["user"]
                   else None)
            if not url or any(p["label"] == label for p in pages):
                continue
            current_page = label
            result = {"label": label, "requested_host": urlsplit(url).hostname,
                      "requested_path": f"/{label}/<id>", "error": None}
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(6500)
                parsed = urlsplit(page.url)
                result.update({"final_host": parsed.hostname,
                               "final_path": safe_path(parsed.path),
                               "captcha_page": "验证码" in page.title()})
            except Exception as exc:
                result["error"] = type(exc).__name__
            pages.append(result)
        ctx.close()
        browser.close()
    # Group identical routes, preserving aggregate statuses and parameter names.
    grouped = {}
    for rec in records.values():
        key = (rec["host"], rec["method"], rec["path"])
        if key not in grouped:
            grouped[key] = {**rec, "pages": [], "statuses": [], "business_codes": [], "count": 0}
            grouped[key].pop("page", None)
            grouped[key].pop("status", None)
            grouped[key].pop("business_code", None)
        val = grouped[key]
        val["count"] += 1
        val["pages"] = sorted(set(val["pages"] + [rec["page"]]))
        val["statuses"] = sorted(set(val["statuses"] + [rec["status"]]), key=lambda x: (x is None, x or 0))
        val["business_codes"] = sorted(set(val["business_codes"] + [rec["business_code"]]), key=str)
        val["query_keys"] = sorted(set(val["query_keys"] + rec["query_keys"]))
        val["body_keys"] = sorted(set(val["body_keys"] + rec["body_keys"]))
    out_file.write_text(json.dumps(sorted(grouped.values(), key=lambda x: (x["host"], x["path"])),
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    pages_file.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pages": pages, "requests": len(records), "routes": len(grouped),
                      "login_proven": login_proven, "video_id_observed": bool(observed_ids["video"]),
                      "user_id_observed": bool(observed_ids["user"])}, ensure_ascii=False))

if __name__ == "__main__":
    sys.exit(main())
