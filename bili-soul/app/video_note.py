"""Save, publish, and verify a Bilibili video note in separate CLI phases.

The CLI reads a Bilibili Cookie file at runtime. Its per-video checkpoint is
stored in ``app/data/``, which is excluded by this app's ``.gitignore``.
Publishing is only performed by an explicit ``publish`` command.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener

from bili_soul.bili_api import BiliAPIError, USER_AGENT, _NoRedirect
from bili_soul.cookies import cookie_header, load_bilibili_cookies


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
API_ROOT = "https://api.bilibili.com"
BVID_RE = re.compile(r"BV[0-9A-Za-z]{10}\Z")
VIDEO_PATH_RE = re.compile(r"/video/(BV[0-9A-Za-z]{10})(?:/|\Z)")
INFO_RETRIES = 8
INFO_RETRY_SECONDS = 0.8


class NoteError(RuntimeError):
    """A note operation failed without exposing account credentials."""

    def __init__(self, message: str, code: int | str | None = None):
        super().__init__(message)
        self.code = code


def parse_bvid(value: str) -> str:
    """Accept an exact BV ID or a canonical Bilibili video URL."""
    if BVID_RE.fullmatch(value):
        return value
    parsed = urlsplit(value)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {
        "bilibili.com", "www.bilibili.com"
    } or parsed.username or parsed.password or parsed.port:
        raise ValueError("请提供 BV 号或 https://www.bilibili.com/video/BV.../ 链接")
    match = VIDEO_PATH_RE.fullmatch(parsed.path)
    if not match:
        raise ValueError("视频链接中没有有效的 BV 号")
    return match.group(1)


def state_path(bvid: str) -> Path:
    if not BVID_RE.fullmatch(bvid):
        raise ValueError("无效 BV 号")
    return DATA_DIR / f"{bvid}.note-state.json"


def load_state(bvid: str) -> dict:
    path = state_path(bvid)
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != 1 or value.get("bvid") != bvid:
        raise NoteError(f"笔记状态文件无效：{path}")
    return value


def save_state(state: dict) -> None:
    path = state_path(state["bvid"])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if os.name != "nt":
        temporary.chmod(0o600)
    os.replace(temporary, path)


@contextmanager
def video_lock(bvid: str):
    """Serialize local CLI invocations for the same video."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{bvid}.note.lock"
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise NoteError("该视频的笔记命令正在运行") from exc
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise NoteError("该视频的笔记命令正在运行") from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def utf16_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def make_ops(text: str, image_url: str = "", image_id: str = "") -> list[dict]:
    """Build Quill Delta content without relying on a particular video."""
    body = text.rstrip("\r\n")
    if not body.strip():
        raise ValueError("笔记正文不能为空")
    ops: list[dict] = [{"insert": body + ("\n\n" if image_url else "\n")}]
    if image_url:
        if not image_id:
            raise ValueError("有图片 URL 时必须有图片 ID")
        ops.extend([
            {"insert": {"imageUpload": {
                "id": image_id, "source": "local", "status": "done",
                "url": image_url, "width": 600,
            }}},
            {"insert": "\n"},
        ])
    return ops


def make_form(state: dict, csrf: str, *, publish: bool = False) -> dict:
    ops = make_ops(state["text"], state.get("image_url", ""), state.get("image_id", ""))
    length = sum(utf16_length(insert) if isinstance(insert, str) else 1
                 for op in ops for insert in [op["insert"]])
    summary = " ".join(state["text"].split())[:70]
    values = {
        "from": "save", "oid": state["aid"], "oid_type": 0,
        "note_id": state.get("note_id") or "", "title": state["title"],
        "summary": summary, "content": json.dumps(ops, ensure_ascii=False, separators=(",", ":")),
        "tags": "", "cls": 1, "csrf": csrf, "cont_len": length,
        "hash": state["hash"], "platform": "web",
    }
    if publish:
        values.update({"publish": 1, "original": 1, "auto_comment": 0, "comment_format": 2})
    return values


def checked_image_url(value: str) -> str:
    """Accept only the image hosts/paths returned by the note upload API."""
    if value.startswith("//"):
        value = "https:" + value
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    hosted_bfs = host.endswith(".hdslb.com") and parsed.path.startswith("/bfs/")
    note_api_image = host == "api.bilibili.com" and parsed.path.startswith("/x/note/image")
    if parsed.scheme != "https" or parsed.username or parsed.password or not (hosted_bfs or note_api_image):
        raise NoteError("图片上传接口返回了非预期 URL")
    return value


def _cookie_file(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for name in ("bilibili-cookies.json", "cookies.txt"):
        candidate = DATA_DIR / name
        if candidate.exists():
            return candidate
    raise NoteError("找不到 B站 Cookie；请将文件放入 app/data/ 或传入 --cookies")


def credentials(cookie_file: Path | None) -> tuple[list[dict], str]:
    cookies = load_bilibili_cookies(_cookie_file(cookie_file))
    csrf = next((item["value"] for item in cookies if item["name"] == "bili_jct"), "")
    if not csrf:
        raise NoteError("B站 Cookie 缺少 bili_jct")
    return cookies, csrf


class NoteClient:
    def __init__(self, bvid: str, cookies: list[dict], csrf: str):
        self.bvid, self.cookies, self.csrf = bvid, cookies, csrf
        self.referer = f"https://www.bilibili.com/video/{bvid}/"

    def request(self, path: str, *, params: dict | None = None, body: bytes | None = None,
                content_type: str | None = None, method: str = "GET") -> dict:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("接口路径必须是 B站 API 的绝对路径")
        url = API_ROOT + path
        if params:
            url += "?" + urlencode(params)
        headers = {
            "User-Agent": USER_AGENT, "Referer": self.referer,
            "Origin": "https://www.bilibili.com", "Accept": "application/json",
            "Cookie": cookie_header(url, self.cookies),
        }
        if content_type:
            headers["Content-Type"] = content_type
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with build_opener(_NoRedirect()).open(request, timeout=30) as response:
                payload = json.load(response)
        except HTTPError as error:
            try:
                payload = json.load(error)
            except (ValueError, OSError) as exc:
                raise NoteError(f"{path}: HTTP {error.code}") from exc
        except (OSError, URLError, ValueError, BiliAPIError) as exc:
            raise NoteError(f"{path}: 请求失败：{exc}") from exc
        if not isinstance(payload, dict) or payload.get("code") != 0:
            code = payload.get("code") if isinstance(payload, dict) else "invalid-json"
            message = payload.get("message") if isinstance(payload, dict) else "invalid JSON"
            raise NoteError(f"{path}: code={code}, message={message}", code)
        return payload.get("data") or {}

    def post_form(self, path: str, values: dict) -> dict:
        return self.request(path, body=urlencode(values).encode("utf-8"),
                            content_type="application/x-www-form-urlencoded", method="POST")

    def nav_mid(self) -> str:
        data = self.request("/x/web-interface/nav")
        if not data.get("isLogin") or not data.get("mid"):
            raise NoteError("B站登录态失效")
        return str(data["mid"])

    def video_identity(self) -> tuple[int, str]:
        data = self.request("/x/web-interface/view", params={"bvid": self.bvid})
        aid = data.get("aid")
        owner_mid = (data.get("owner") or {}).get("mid")
        if not aid or not owner_mid or data.get("bvid") != self.bvid:
            raise NoteError("视频信息缺少 aid、作者 MID 或 BV 号不匹配")
        return int(aid), str(owner_mid)

    def note_ids(self, aid: int) -> list[str]:
        data = self.request("/x/note/list/archive", params={
            "oid": aid, "oid_type": 0, "csrf": self.csrf,
        })
        return [str(item) for item in (data.get("noteIds") or [])]

    def upload_image(self, image_path: Path) -> str:
        image_path = image_path.expanduser().resolve(strict=True)
        if not image_path.is_file():
            raise NoteError("配图不是文件")
        mime = mimetypes.guess_type(image_path.name)[0]
        if mime not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
            raise NoteError("配图格式需为 PNG、JPEG、WebP 或 GIF")
        boundary = "----bilisoul-" + uuid.uuid4().hex
        filename = image_path.name.replace('"', "_").replace("\r", "_").replace("\n", "_")
        parts = [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf\"\r\n\r\n{self.csrf}\r\n".encode(),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{filename}\"\r\nContent-Type: {mime}\r\n\r\n".encode(),
            image_path.read_bytes(),
            f"\r\n--{boundary}--\r\n".encode(),
        ]
        data = self.request("/x/note/image/upload", body=b"".join(parts),
                            content_type=f"multipart/form-data; boundary={boundary}", method="POST")
        return checked_image_url(str(data.get("location") or ""))

    def note_info(self, aid: int, note_id: str) -> dict:
        for attempt in range(INFO_RETRIES):
            try:
                return self.request("/x/note/info", params={
                    "oid": aid, "oid_type": 0, "note_id": note_id, "csrf": self.csrf,
                })
            except NoteError as exc:
                if exc.code != 79502 or attempt == INFO_RETRIES - 1:
                    raise
                time.sleep(INFO_RETRY_SECONDS)
        raise AssertionError("unreachable")


def verify_content(data: dict, state: dict) -> None:
    if str(data.get("note_id") or state["note_id"]) != str(state["note_id"]):
        raise NoteError("笔记回读 ID 不匹配")
    if data.get("title") != state["title"]:
        raise NoteError("笔记回读标题不匹配")
    raw = data.get("content")
    try:
        ops = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError as exc:
        raise NoteError("笔记回读正文不是有效 JSON") from exc
    if not isinstance(ops, list):
        raise NoteError("笔记回读正文不是 Delta 数组")
    text = "".join(op.get("insert", "") for op in ops
                   if isinstance(op, dict) and isinstance(op.get("insert"), str))
    if state["text"].rstrip("\r\n") not in text:
        raise NoteError("笔记回读正文不匹配")
    images = [op["insert"]["imageUpload"].get("url") for op in ops
              if isinstance(op, dict) and isinstance(op.get("insert"), dict)
              and isinstance(op["insert"].get("imageUpload"), dict)]
    if state.get("image_url") and state["image_url"] not in images:
        raise NoteError("笔记回读缺少配图")


def _check_account(state: dict, mid: str) -> None:
    if str(state.get("login_mid")) != mid:
        raise NoteError("当前登录账号与保存笔记的账号不同")


def _private_readback(client: NoteClient, state: dict) -> dict:
    data = client.note_info(state["aid"], state["note_id"])
    verify_content(data, state)
    status = data.get("pub_status")
    if status is not None and str(status) != "0":
        raise NoteError(f"笔记已不处于私人状态：pub_status={status}")
    return data


def _recover_save(client: NoteClient, state: dict) -> bool:
    """Resolve an ambiguous private-save response without issuing another POST."""
    ids = client.note_ids(state["aid"])
    matching = []
    for note_id in ids:
        try:
            data = client.note_info(state["aid"], note_id)
        except NoteError as exc:
            if exc.code == 79502:
                continue
            raise
        candidate = {**state, "note_id": note_id}
        try:
            verify_content(data, candidate)
        except NoteError:
            continue
        matching.append(note_id)
    if len(matching) == 1:
        state["note_id"] = matching[0]
        state["phase"] = "saved_response"
        save_state(state)
        return True
    raise NoteError("保存请求结果不明确；未重试写入。请稍后再运行 save 进行只读回查")


def save_private(client: NoteClient, title: str | None, text_file: Path | None,
                 image_path: Path | None) -> dict:
    mid = client.nav_mid()
    state = load_state(client.bvid)
    if state:
        _check_account(state, mid)
        if title is not None and title != state["title"]:
            raise NoteError("状态文件中的标题与本次参数不同")
        if text_file is not None and text_file.read_text(encoding="utf-8-sig") != state["text"]:
            raise NoteError("状态文件中的正文与本次文件不同")
        if image_path is not None and str(image_path.expanduser().resolve()) != state.get("image_path"):
            raise NoteError("状态文件中的配图路径与本次参数不同")
    else:
        if not title or not title.strip() or text_file is None:
            raise NoteError("首次 save 必须提供 --title 和 --text-file")
        body = text_file.read_text(encoding="utf-8-sig")
        make_ops(body)  # Reject empty input before any network write.
        aid, owner_mid = client.video_identity()
        forbid = client.request("/x/note/is_forbid", params={"aid": aid})
        if forbid.get("forbid_note_entrance"):
            raise NoteError("该视频禁止创建笔记")
        if client.note_ids(aid):
            raise NoteError("当前账号已在该视频创建笔记；停止以免覆盖")
        state = {
            "schema": 1, "bvid": client.bvid, "aid": aid, "owner_mid": owner_mid,
            "login_mid": mid, "title": title.strip(), "text": body,
            "image_path": str(image_path.expanduser().resolve()) if image_path else "",
            "image_id": f"IMAGE_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}" if image_path else "",
            "hash": int(time.time() * 1000), "phase": "prepared",
        }
        save_state(state)

    if state.get("phase") in {"private_verified", "publish_attempted", "publish_submitted", "public_verified"}:
        return state
    if state.get("phase") == "save_attempted" and not state.get("note_id"):
        _recover_save(client, state)
    if not state.get("note_id"):
        if state.get("image_path") and not state.get("image_url"):
            state["image_url"] = client.upload_image(Path(state["image_path"]))
            state["phase"] = "image_uploaded"
            save_state(state)
        # Checkpoint before POST. An ambiguous response will only be recovered by GET.
        state["phase"] = "save_attempted"
        save_state(state)
        response = client.post_form("/x/note/add", make_form(state, client.csrf))
        if not response.get("note_id"):
            raise NoteError("保存返回成功，但没有 note_id；请再次运行 save 回查")
        state["note_id"] = str(response["note_id"])
        state["phase"] = "saved_response"
        save_state(state)
    data = _private_readback(client, state)
    state["phase"] = "private_verified"
    state["pub_status"] = data.get("pub_status")
    save_state(state)
    return state


def publish(client: NoteClient) -> dict:
    state = load_state(client.bvid)
    if not state or not state.get("note_id"):
        raise NoteError("没有已保存的笔记；先运行 save")
    _check_account(state, client.nav_mid())
    if state.get("phase") in {"publish_attempted", "publish_submitted", "public_verified"}:
        return state
    if state.get("phase") != "private_verified":
        raise NoteError("必须先完成私人笔记回读，才能公开发布")
    _private_readback(client, state)
    state["phase"] = "publish_attempted"
    save_state(state)
    response = client.post_form("/x/note/add", make_form(state, client.csrf, publish=True))
    state["phase"] = "publish_submitted"
    state["publish_response_status"] = response.get("pub_status")
    save_state(state)
    return state


def _public_link(client: NoteClient, state: dict, mid: str) -> tuple[str, str]:
    for page in range(1, 11):
        listing = client.request("/x/note/publish/list/archive", params={
            "oid": state["aid"], "oid_type": 0, "pn": page, "ps": 20,
            "uper_mid": state["owner_mid"],
        })
        items = listing.get("list") or []
        for item in items:
            if str((item.get("author") or {}).get("mid")) != mid:
                continue
            cvid, web_url = item.get("cvid"), item.get("web_url")
            if not cvid or not web_url:
                continue
            public = client.request("/x/note/publish/info", params={"cvid": cvid})
            if public.get("title") != state["title"] or str(public.get("note_id")) != str(state["note_id"]):
                continue
            parsed = urlsplit(web_url)
            if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {
                "bilibili.com", "www.bilibili.com",
            }:
                raise NoteError("公开笔记接口返回了非预期链接")
            return str(cvid), web_url
        if len(items) < 20:
            break
    raise NoteError("笔记已显示审核通过，但尚未在公开视频笔记列表中找到；请稍后再运行 verify")


def verify(client: NoteClient) -> dict:
    state = load_state(client.bvid)
    if not state or not state.get("note_id"):
        raise NoteError("没有已保存的笔记；先运行 save")
    mid = client.nav_mid()
    _check_account(state, mid)
    data = client.note_info(state["aid"], state["note_id"])
    verify_content(data, state)
    state["pub_status"] = data.get("pub_status")
    state["pub_reason"] = data.get("pub_reason")
    save_state(state)
    if str(state["pub_status"]) == "2":
        cvid, link = _public_link(client, state, mid)
        state.update({"cvid": cvid, "web_url": link, "public_verified": True,
                      "phase": "public_verified"})
    elif state.get("phase") == "public_verified":
        state["public_verified"] = False
        state["phase"] = "publish_submitted"
    save_state(state)
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("save", "publish", "verify"))
    parser.add_argument("video", help="BV 号或 https://www.bilibili.com/video/BV.../ 链接")
    parser.add_argument("--cookies", type=Path, help="B站 JSON 或 Netscape Cookie 文件；默认 app/data/")
    parser.add_argument("--title", help="首次 save 的笔记标题")
    parser.add_argument("--text-file", type=Path, help="首次 save 的 UTF-8 纯文本正文")
    parser.add_argument("--image", type=Path, help="首次 save 的可选配图")
    args = parser.parse_args(argv)
    if args.phase != "save" and (args.title or args.text_file or args.image):
        parser.error("--title、--text-file、--image 仅用于 save")
    try:
        bvid = parse_bvid(args.video)
        with video_lock(bvid):
            cookies, csrf = credentials(args.cookies)
            client = NoteClient(bvid, cookies, csrf)
            if args.phase == "save":
                state = save_private(client, args.title, args.text_file, args.image)
            elif args.phase == "publish":
                state = publish(client)
            else:
                state = verify(client)
    except (NoteError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    result = {"bvid": bvid, "phase": state["phase"], "note_id": state.get("note_id"),
              "pub_status": state.get("pub_status")}
    if state.get("public_verified"):
        result["public_url"] = state["web_url"]
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
