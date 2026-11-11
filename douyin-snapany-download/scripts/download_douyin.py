#!/usr/bin/env python3
"""Download Douyin and Bilibili videos through SnapAny's web page workflow."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import html
import ipaddress
import json
import os
import queue
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


WEB_PAGE = "https://snapany.com/zh/tiktok-video-download"
EXTRACT_ENDPOINT = "https://api.snapany.com/v1/extract/post"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)
URL_RE = re.compile(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&()*+,;=%]+", re.IGNORECASE)
CHUNK_RE = re.compile(r"/_next/static/chunks/[^\s\"'<>]+?\.js")
SIGNER_RE = re.compile(
    r'crypto\.subtle\.importKey\("raw",[\w$]+\.encode\("([^"\\]{20,100})"\),'
    r'\{name:"HMAC",hash:"SHA-256"\}'
)
TRAILING_PUNCTUATION = ".,;!?)]}。，、；！？）】」』"
MAX_PAGE_BYTES = 3 * 1024 * 1024
MAX_CHUNK_BYTES = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class DownloadError(Exception):
    """A user-facing download failure that contains no credentials or signed URL."""


class QuotaError(DownloadError):
    """The website's free extraction limit has been reached."""


def platform_for_url(value: str) -> str | None:
    """Classify an allowed video URL without accepting lookalike hostnames."""
    try:
        parts = urllib.parse.urlsplit(value)
        host = (parts.hostname or "").lower()
    except ValueError:
        return None
    if parts.scheme.lower() not in ("http", "https") or parts.username or parts.password:
        return None
    if (host == "douyin.com" or host.endswith(".douyin.com")
            or host == "iesdouyin.com" or host.endswith(".iesdouyin.com")):
        return "douyin"
    if host == "bilibili.com" or host.endswith(".bilibili.com") or host == "b23.tv":
        return "bilibili"
    return None


def _matching_urls(share_text: str, platforms: set[str]) -> list[str]:
    urls = []
    for match in URL_RE.finditer(share_text):
        value = match.group(0).rstrip(TRAILING_PUNCTUATION)
        if platform_for_url(value) in platforms and value not in urls:
            urls.append(value)
    return urls


def video_urls(share_text: str) -> list[str]:
    """Return supported video URLs from share text in their original order."""
    urls = _matching_urls(share_text, {"douyin", "bilibili"})
    if not urls:
        raise DownloadError("未找到抖音或 B站视频链接。")
    return urls


def douyin_urls(share_text: str) -> list[str]:
    """Keep the original Douyin-only helper available to existing callers."""
    urls = _matching_urls(share_text, {"douyin"})
    if not urls:
        raise DownloadError("未找到抖音视频链接。")
    return urls


def douyin_url(share_text: str) -> str:
    """Return the first Douyin URL in a share message."""
    return douyin_urls(share_text)[0]


def read_small(url: str, limit: int, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(limit + 1)
    except (OSError, TimeoutError) as exc:
        raise DownloadError("无法连接 SnapAny 网页或接口。") from exc
    if len(data) > limit:
        raise DownloadError("SnapAny 返回的数据过大，已停止解析。")
    return data


def current_signer() -> bytes:
    """Read the current public signing material from SnapAny's loaded page JS."""
    page = read_small(WEB_PAGE, MAX_PAGE_BYTES).decode("utf-8", "replace")
    paths = list(dict.fromkeys(html.unescape(p) for p in CHUNK_RE.findall(page)))
    if not paths:
        raise DownloadError("无法从 SnapAny 网页找到解析脚本。")
    # The observed build places the signer in this chunk. Scan other page chunks
    # if a later build moves it; never persist or display the signing material.
    paths.sort(key=lambda p: 0 if re.search(r"/5727-[^/]+\.js$", p) else 1)
    for path in paths:
        url = urllib.parse.urljoin(WEB_PAGE, path)
        if urllib.parse.urlsplit(url).hostname != "snapany.com":
            continue
        try:
            script = read_small(url, MAX_CHUNK_BYTES).decode("utf-8", "replace")
        except DownloadError:
            continue
        match = SIGNER_RE.search(script)
        if match and "extract.post.$post" in script[match.end():match.end() + 1200]:
            return match.group(1).encode("utf-8")
    raise DownloadError("SnapAny 网页签名方式已变化，当前技能需要更新。")


def extract_video(link: str) -> tuple[str, dict]:
    signer = current_signer()
    locale = "zh"
    timestamp = str(int(time.time() * 1000))
    signature = hmac.new(
        signer, (link + locale + timestamp).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    body = json.dumps({"link": link}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        EXTRACT_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Accept": "*/*",
            "Accept-Language": locale,
            "Content-Type": "application/json",
            "G-Api-Version": "2",
            "G-Timestamp": timestamp,
            "G-Footer": signature,
            "G-Timezone": "Asia/Shanghai",
            "Origin": "https://snapany.com",
            "Referer": "https://snapany.com/",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        error_code = None
        try:
            response = json.loads(exc.read(8192))
            if isinstance(response, dict):
                candidate = response.get("code")
                if isinstance(candidate, str) and re.fullmatch(r"[a-z0-9_]{1,64}", candidate):
                    error_code = candidate
        except (ValueError, OSError):
            pass
        if error_code == "free_limit_exceeded":
            raise QuotaError("SnapAny 网页免费解析额度已用完，请在额度恢复后重试。") from exc
        detail = f"；{error_code}" if error_code else ""
        raise DownloadError(f"SnapAny 解析失败（HTTP {exc.code}{detail}）。") from exc
    except (OSError, TimeoutError) as exc:
        raise DownloadError("无法连接 SnapAny 解析接口。") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise DownloadError("SnapAny 解析响应过大。")
    try:
        post = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise DownloadError("SnapAny 返回了无效的解析结果。") from exc
    if not isinstance(post, dict):
        raise DownloadError("SnapAny 返回了无效的解析结果。")
    medias = post.get("medias")
    if not isinstance(medias, list):
        raise DownloadError("SnapAny 解析结果没有媒体列表。")
    video = next(
        (m for m in medias if isinstance(m, dict)
         and m.get("media_type") == "video"),
        None,
    )
    if video is None:
        site = "B站" if platform_for_url(link) == "bilibili" else "抖音"
        raise DownloadError(f"这个{site}链接没有可下载的视频，可能是图文内容。")
    return str(post.get("id") or ""), video


def _valid_media_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
        scheme = parsed.scheme.lower()
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        return False
    if scheme not in ("https", "http") or not host or parsed.username or parsed.password:
        return False
    if port == 0 or (port is None and parsed.netloc.endswith(":")):
        return False
    if (host == "localhost" or host.endswith(".localhost")
            or host.endswith(".local") or host.endswith(".internal")):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # Reject numeric spellings that some HTTP stacks treat as loopback.
        if "." not in host or re.fullmatch(r"[0-9.]+", host) or host.startswith("0x"):
            return False
        proxies = urllib.request.getproxies()
        proxy_resolves_host = (
            not urllib.request.proxy_bypass(host)
            and bool(proxies.get(scheme) or proxies.get("all"))
        )
        answer = queue.Queue(maxsize=1)

        def resolve():
            try:
                answer.put(socket.getaddrinfo(
                    host, port or (443 if scheme == "https" else 80),
                    type=socket.SOCK_STREAM,
                ))
            except OSError:
                answer.put(None)

        threading.Thread(target=resolve, daemon=True).start()
        try:
            addresses = answer.get(timeout=5)
        except queue.Empty:
            return proxy_resolves_host
        if not addresses:
            # A configured HTTP(S) proxy may resolve a public domain remotely.
            return proxy_resolves_host
        try:
            return all(ipaddress.ip_address(item[4][0]).is_global for item in addresses)
        except (ValueError, IndexError, TypeError):
            return False
    else:
        return address.is_global


class _SafeMediaRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if not _valid_media_url(newurl):
            raise DownloadError("媒体地址重定向到不安全的位置。")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


_MEDIA_OPENER = urllib.request.build_opener(_SafeMediaRedirectHandler)


def _media_headers(video: dict, platform: str) -> dict[str, str]:
    headers = video.get("headers") or {}
    if not isinstance(headers, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in headers.items()
    ):
        raise DownloadError("SnapAny 返回了无效的媒体请求头。")
    allowed = {"user-agent": "User-Agent", "referer": "Referer"}
    if platform == "douyin":
        allowed.update({"origin": "Origin", "accept": "Accept",
                        "accept-language": "Accept-Language"})
    public_headers = {}
    for key, value in headers.items():
        canonical = allowed.get(key.lower())
        if canonical is not None:
            if len(value) > 2048 or any(character in value for character in "\r\n\x00"):
                raise DownloadError("SnapAny 返回了无效的媒体请求头。")
            public_headers[canonical] = value
    return public_headers


def choose_bilibili_source(video: dict, ffmpeg_available: bool) -> tuple[str, object]:
    """Prefer the default separate tracks; otherwise verify the direct MP4 later."""
    variants = video.get("variants")
    if ffmpeg_available and isinstance(variants, list):
        default = next(
            (v for v in variants if isinstance(v, dict) and v.get("is_default") is True),
            None,
        )
        if (default is not None and _valid_media_url(default.get("video_url"))
                and _valid_media_url(default.get("audio_url"))):
            return "mux", default
    resource_url = video.get("resource_url")
    if _valid_media_url(resource_url):
        return "resource", resource_url
    if not ffmpeg_available:
        raise DownloadError("B站视频需要 ffmpeg 合并音视频，且 SnapAny 没有提供备用 MP4。")
    raise DownloadError("SnapAny 没有提供可用的 B站完整视频地址。")


def _download_media(url: str, path: Path, headers: dict[str, str]) -> None:
    """Stream one media URL to a temporary file without exposing its signed URL."""
    if not _valid_media_url(url):
        raise DownloadError("SnapAny 返回了不安全的媒体地址。")
    request = urllib.request.Request(url, headers=headers)
    try:
        response = _MEDIA_OPENER.open(request, timeout=60)
    except urllib.error.HTTPError as exc:
        raise DownloadError(f"视频下载失败（HTTP {exc.code}）。") from exc
    except (OSError, TimeoutError) as exc:
        raise DownloadError("视频下载连接失败。") from exc
    with response:
        content_type = response.headers.get_content_type().lower()
        try:
            first_chunk = response.read(1024 * 1024)
        except OSError as exc:
            raise DownloadError("视频下载连接中断。") from exc
        if (
            not first_chunk
            or content_type.startswith("text/")
            or content_type in ("application/json", "application/xml")
            or first_chunk[:128].lstrip().lower().startswith(
                (b"<!doctype html", b"<html", b"{\"error\"", b"{\"code\"")
            )
        ):
            raise DownloadError("媒体地址返回了网页或错误信息。")
        try:
            with path.open("xb") as target:
                target.write(first_chunk)
                while True:
                    try:
                        chunk = response.read(1024 * 1024)
                    except OSError as exc:
                        raise DownloadError("视频下载连接中断。") from exc
                    if not chunk:
                        break
                    target.write(chunk)
        except BaseException:
            path.unlink(missing_ok=True)
            raise


def _boxes(source, start: int, end: int):
    """Iterate MP4 boxes by seeking over media payloads instead of loading them."""
    cursor = start
    count = 0
    while cursor + 8 <= end and count < 10000:
        source.seek(cursor)
        header = source.read(8)
        if len(header) != 8:
            return
        size, kind = struct.unpack(">I4s", header)
        header_size = 8
        if size == 1:
            extension = source.read(8)
            if len(extension) != 8:
                return
            size = struct.unpack(">Q", extension)[0]
            header_size = 16
        elif size == 0:
            size = end - cursor
        if size < header_size or size > end - cursor:
            return
        box_end = cursor + size
        yield kind, cursor + header_size, box_end
        cursor = box_end
        count += 1


def mp4_has_video_and_audio(path: Path) -> bool:
    """Require both tracks before delivering a Bilibili MP4."""
    file_size = path.stat().st_size
    has_ftyp = False
    track_types = set()
    with path.open("rb") as source:
        for kind, payload, box_end in _boxes(source, 0, file_size):
            if kind == b"ftyp":
                has_ftyp = True
            if kind != b"moov":
                continue
            for child_kind, child_payload, child_end in _boxes(source, payload, box_end):
                if child_kind != b"trak":
                    continue
                for track_kind, track_payload, track_end in _boxes(source, child_payload, child_end):
                    if track_kind != b"mdia":
                        continue
                    for media_kind, handler_payload, handler_end in _boxes(
                        source, track_payload, track_end
                    ):
                        if media_kind == b"hdlr" and handler_end - handler_payload >= 12:
                            source.seek(handler_payload + 8)
                            track_types.add(source.read(4))
    return has_ftyp and {b"vide", b"soun"}.issubset(track_types)


def _publish_media(source: Path, output_dir: Path, post_id: str) -> Path:
    """Publish a completed Bilibili MP4 without replacing an earlier download."""
    for number in range(1, 1000):
        suffix = "" if number == 1 else f"-{number}"
        path = output_dir / f"bilibili-{post_id}{suffix}.mp4"
        try:
            os.link(source, path)
            return path
        except FileExistsError:
            continue
        except OSError:
            try:
                with path.open("xb") as target, source.open("rb") as original:
                    shutil.copyfileobj(original, target, 1024 * 1024)
                return path
            except FileExistsError:
                continue
            except BaseException:
                path.unlink(missing_ok=True)
                raise
    raise DownloadError("同一视频已有过多同名文件。")


def _download_bilibili(post_id: str, video: dict, output_dir: Path,
                       headers: dict[str, str]) -> Path:
    ffmpeg_path = shutil.which("ffmpeg")
    source_type, source = choose_bilibili_source(video, bool(ffmpeg_path))
    with tempfile.TemporaryDirectory(prefix=".bilibili-", dir=output_dir) as folder:
        temporary = Path(folder)
        complete = temporary / "complete.mp4"
        mux_failure = None
        if source_type == "mux":
            try:
                video_track = temporary / "video.mp4"
                audio_track = temporary / "audio.m4a"
                _download_media(source["video_url"], video_track, headers)
                _download_media(source["audio_url"], audio_track, headers)
                try:
                    result = subprocess.run(
                        [ffmpeg_path, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                         "-i", str(video_track), "-i", str(audio_track),
                         "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
                         "-movflags", "+faststart", str(complete)],
                        capture_output=True, timeout=3600, check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise DownloadError("ffmpeg 合并 B站音视频失败。") from exc
                if (result.returncode != 0 or not complete.is_file()
                        or complete.stat().st_size == 0):
                    raise DownloadError("ffmpeg 合并 B站音视频失败。")
                if not mp4_has_video_and_audio(complete):
                    raise DownloadError("合并后的 B站 MP4 缺少视频或音轨。")
            except DownloadError as exc:
                mux_failure = exc
                resource_url = video.get("resource_url")
                if not _valid_media_url(resource_url):
                    raise DownloadError("B站高清分轨失败，且没有备用 MP4。") from exc
                source = resource_url
                complete.unlink(missing_ok=True)
        if source_type == "resource" or mux_failure is not None:
            try:
                _download_media(source, complete, headers)
            except DownloadError as exc:
                if mux_failure is not None:
                    raise DownloadError("B站高清分轨和备用 MP4 均下载失败。") from exc
                raise
            if not mp4_has_video_and_audio(complete):
                if mux_failure is not None:
                    raise DownloadError("B站高清分轨失败，备用 MP4 也缺少视频或音轨。")
                if ffmpeg_path:
                    raise DownloadError("SnapAny 返回的 B站备用 MP4 缺少视频或音轨。")
                raise DownloadError("B站备用 MP4 缺少视频或音轨；请安装 ffmpeg 合并音视频。")
        return _publish_media(complete, output_dir, post_id)


def download(link: str, output_dir: Path) -> Path:
    post_id, video = extract_video(link)
    if not re.fullmatch(r"\d{6,30}", post_id):
        post_id = hashlib.sha256(link.encode("utf-8")).hexdigest()[:12]
    output_dir.mkdir(parents=True, exist_ok=True)
    platform = platform_for_url(link)
    media_headers = _media_headers(video, platform)
    if platform == "bilibili":
        return _download_bilibili(post_id, video, output_dir, media_headers)
    resource_url = video.get("resource_url")
    if not _valid_media_url(resource_url):
        raise DownloadError("SnapAny 返回了无效的视频地址。")
    request = urllib.request.Request(resource_url, headers=media_headers)
    try:
        response = _MEDIA_OPENER.open(request, timeout=60)
    except urllib.error.HTTPError as exc:
        raise DownloadError(f"视频下载失败（HTTP {exc.code}）。") from exc
    except (OSError, TimeoutError) as exc:
        raise DownloadError("视频下载连接失败。") from exc
    with response:
        content_type = response.headers.get_content_type().lower()
        try:
            first_chunk = response.read(1024 * 1024)
        except OSError as exc:
            raise DownloadError("视频下载连接中断。") from exc
        if (
            not first_chunk
            or content_type.startswith("text/")
            or content_type in ("application/json", "application/xml")
            or first_chunk[:128].lstrip().lower().startswith(
                (b"<!doctype html", b"<html", b"{\"error\"", b"{\"code\"")
            )
        ):
            raise DownloadError("视频地址返回了网页或错误信息，没有保存为 MP4。")
        # Exclusive creation protects an existing download with the same post ID.
        for number in range(1, 1000):
            suffix = "" if number == 1 else f"-{number}"
            path = output_dir / f"douyin-{post_id}{suffix}.mp4"
            try:
                target = path.open("xb")
                break
            except FileExistsError:
                continue
        else:
            raise DownloadError("同一视频已有过多同名文件。")
        try:
            with target:
                target.write(first_chunk)
                while True:
                    try:
                        chunk = response.read(1024 * 1024)
                    except OSError as exc:
                        raise DownloadError("视频下载连接中断。") from exc
                    if not chunk:
                        break
                    target.write(chunk)
            if path.stat().st_size == 0:
                raise DownloadError("视频文件为空。")
        except BaseException:
            path.unlink(missing_ok=True)
            raise
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="通过 SnapAny 网页接口下载抖音或 B站视频")
    parser.add_argument("share_text", nargs="+", help="抖音或 B站视频链接，或包含链接的分享文案")
    parser.add_argument(
        "--output-dir", type=Path, default=Path.home() / "Downloads", help="保存目录（默认下载目录）"
    )
    args = parser.parse_args()
    try:
        urls = video_urls(" ".join(args.share_text))
    except DownloadError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    failed = False
    for index, url in enumerate(urls, start=1):
        try:
            path = download(url, args.output_dir)
        except QuotaError as exc:
            print(f"第 {index} 条链接失败：{exc}", file=sys.stderr)
            return 1
        except DownloadError as exc:
            print(f"第 {index} 条链接失败：{exc}", file=sys.stderr)
            failed = True
        except OSError as exc:
            print(f"第 {index} 条链接失败：无法写入视频文件（{type(exc).__name__}）。", file=sys.stderr)
            failed = True
        else:
            print(path.resolve())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
