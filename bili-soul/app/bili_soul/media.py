import os
import re
import shlex
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from .cookies import load_bilibili_cookies
from .logging import say


SUBTITLE_LANGUAGES = "zh.*,ai-zh.*,en.*"
AUDIO_EXTENSIONS = {".m4a", ".mp3", ".aac", ".opus", ".ogg", ".flac", ".wav", ".webm", ".mp4", ".mkv"}
DEFAULT_REMOTE_HOST = ""
DEFAULT_REMOTE_TOOLKIT = "/path/to/VideoSrtToolkit"
SSH_OPTIONS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
               "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3"]


def _run(cmd, *, timeout=3600):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def _error(result):
    return (result.stderr or result.stdout or "命令执行失败").strip()[-1500:]


@contextmanager
def _yt_dlp_args():
    """Give yt-dlp only validated Bilibili cookies, in a short-lived jar."""
    common = [sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-playlist",
              "--no-warnings"]
    cookies = load_bilibili_cookies()
    if not cookies:
        yield common
        return
    Path("data").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bilisoul-cookies-", dir="data") as temp:
        cookie_file = Path(temp) / "cookies.txt"
        rows = ["# Netscape HTTP Cookie File"]
        for cookie in cookies:
            name, value = cookie["name"], cookie["value"]
            if "\t" in name or "\t" in value:
                raise ValueError("Cookie 名称或值包含无效制表符")
            domain = cookie["domain"]
            host_only = "FALSE" if domain.startswith(".") else "TRUE"
            netscape_domain = ("#HttpOnly_" if cookie.get("httpOnly") else "") + domain
            rows.append("\t".join((netscape_domain, "FALSE" if host_only == "TRUE" else "TRUE",
                                   cookie.get("path") or "/", "TRUE" if cookie.get("secure") else "FALSE",
                                   str(int(cookie.get("expires") or 0)), name, value)))
        cookie_file.write_text("\n".join(rows) + "\n", encoding="utf-8")
        yield [*common, "--cookies", str(cookie_file.resolve())]


def _subtitle_files(folder):
    srts = sorted((p for p in folder.glob("*.srt") if p.is_file()),
                  key=lambda p: (p.name != "transcript.srt", p.name))
    vtts = sorted((p for p in folder.glob("*.vtt") if p.is_file()), key=lambda p: p.name)
    return srts + vtts


def _usable_subtitle(path):
    try:
        return "-->" in path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return False

def download_video(url, bvid):
    """Fetch provider subtitles first; download audio only when none are available."""
    if not re.fullmatch(r"BV[0-9A-Za-z]+", bvid):
        raise ValueError("无效的 B 站 BV 号")
    folder = Path("downloads") / bvid
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / "transcript.srt").is_file():
        return folder
    if any(_usable_subtitle(p) for p in _subtitle_files(folder)):
        return folder

    with _yt_dlp_args() as common:
        say("字幕", "先尝试提取 B 站已有字幕，不下载视频")
        result = _run([*common, "--skip-download", "--write-subs", "--write-auto-subs",
                       "--sub-langs", SUBTITLE_LANGUAGES, "--sub-format", "srt/vtt/best",
                       "-o", str(folder / "video.%(ext)s"), url])
        if any(_usable_subtitle(p) for p in _subtitle_files(folder)):
            return folder
        if result.returncode:
            say("字幕", f"字幕提取未成功：{_error(result)}", "yellow")

        if any(p.is_file() and p.name.startswith("audio.") and p.suffix.lower() in AUDIO_EXTENSIONS
               for p in folder.iterdir()):
            return folder
        say("音频", "没有可用字幕，下载最佳音轨用于转录", "yellow")
        result = _run([*common, "-f", "bestaudio", "-o", str(folder / "audio.%(ext)s"), url])
        if result.returncode:
            raise RuntimeError(f"下载音频失败：{_error(result)}")
        if not any(p.is_file() and p.name.startswith("audio.") and p.suffix.lower() in AUDIO_EXTENSIONS
                   for p in folder.iterdir()):
            raise RuntimeError("音频下载命令完成，但未找到音频文件")
    return folder

_VTT_TIME = re.compile(r"(?:(\d{2}):)?(\d{2}):(\d{2})[.,](\d{3})$")


def _srt_time(value):
    match = _VTT_TIME.fullmatch(value.strip())
    if not match:
        raise ValueError(f"无效的字幕时间戳：{value}")
    hours, minutes, seconds, millis = match.groups()
    return f"{hours or '00'}:{minutes}:{seconds},{millis}"


def vtt_to_srt(path):
    rows = []
    cue_count = 0
    content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    for block in re.split(r"\n\s*\n", content):
        lines = block.splitlines()
        time_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_index is None:
            continue
        start, end = lines[time_index].split("-->", 1)
        try:
            timing = f"{_srt_time(start)} --> {_srt_time(end.strip().split()[0])}"
        except (ValueError, IndexError):
            continue
        text_lines = [line for line in lines[time_index + 1:] if line.strip()]
        if text_lines:
            cue_count += 1
            rows.extend([str(cue_count), timing, *text_lines, ""])
    out = path.with_suffix(".srt")
    out.write_text("\n".join(rows), encoding="utf-8")
    return out

def _remote_transcript(media, folder):
    host = os.getenv("REMOTE_TRANSCRIBE_HOST", DEFAULT_REMOTE_HOST).strip()
    if not host:
        raise RuntimeError("远程转录未配置")
    if not re.fullmatch(r"[A-Za-z0-9_.@-]+", host) or host.startswith("-"):
        raise ValueError("REMOTE_TRANSCRIBE_HOST 无效")
    toolkit = os.getenv("REMOTE_TRANSCRIBE_TOOLKIT_DIR", DEFAULT_REMOTE_TOOLKIT).strip()
    if not toolkit.startswith("/"):
        raise ValueError("REMOTE_TRANSCRIBE_TOOLKIT_DIR 必须是远程绝对路径")
    remote_dir = f"/tmp/bilisoul-{uuid.uuid4().hex}"
    remote_media = f"{remote_dir}/{media.name}"
    remote_srt = f"{remote_dir}/{media.stem}.srt"
    local_tmp = folder / "transcript.remote.tmp"
    local_srt = folder / "transcript.srt"
    created = False

    def ssh(command, *, timeout=3600):
        result = _run(["ssh", *SSH_OPTIONS, host, command], timeout=timeout)
        if result.returncode:
            raise RuntimeError(_error(result))
        return result

    def scp(source, target):
        result = _run(["scp", "-q", *SSH_OPTIONS, source, target], timeout=1200)
        if result.returncode:
            raise RuntimeError(_error(result))

    try:
        ssh(f"mkdir -m 700 -- {shlex.quote(remote_dir)}", timeout=30)
        created = True
        scp(str(media.resolve()), f"{host}:{remote_media}")
        model = os.getenv("WHISPER_MODEL", "small")
        command = (f"cd -- {shlex.quote(toolkit)} && "
                   f".venv/bin/python -m video_srt transcribe {shlex.quote(remote_media)} "
                   f"--output-dir {shlex.quote(remote_dir)} --model {shlex.quote(model)} "
                   "--device cpu --compute-type int8 --language zh --local-files-only")
        ssh(command)
        scp(f"{host}:{remote_srt}", str(local_tmp.resolve()))
        if not _usable_subtitle(local_tmp):
            say("转录", "首次语音检测未识别到内容，关闭 VAD 再试一次", "yellow")
            ssh(command + " --no-vad --overwrite")
            scp(f"{host}:{remote_srt}", str(local_tmp.resolve()))
        if not _usable_subtitle(local_tmp):
            say("转录", "音轨未识别到可用语音，保存空字幕", "yellow")
        local_tmp.replace(local_srt)
        return local_srt
    finally:
        local_tmp.unlink(missing_ok=True)
        if created:
            try:
                ssh(f"rm -r -- {shlex.quote(remote_dir)}", timeout=30)
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                say("转录", f"远程临时目录清理失败：{exc}", "yellow")


def _local_transcript(media, folder):
    from faster_whisper import WhisperModel

    model = WhisperModel(os.getenv("WHISPER_MODEL", "small"),
                         device=os.getenv("WHISPER_DEVICE", "cpu"),
                         compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"))
    segments, _ = model.transcribe(str(media), language="zh", vad_filter=True)
    rows = []
    for i, segment in enumerate(segments, 1):
        def ts(sec):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = sec % 60
            return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")
        rows.extend([str(i), f"{ts(segment.start)} --> {ts(segment.end)}",
                     segment.text.strip(), ""])
    srt = folder / "transcript.srt"
    srt.write_text("\n".join(rows), encoding="utf-8")
    return srt


def transcript(folder):
    folder = Path(folder)
    cached = folder / "transcript.srt"
    if cached.is_file():
        return cached, cached.read_text(encoding="utf-8", errors="replace")
    for path in _subtitle_files(folder):
        if not _usable_subtitle(path):
            continue
        srt = vtt_to_srt(path) if path.suffix.lower() == ".vtt" else path
        if not _usable_subtitle(srt):
            continue
        return srt, srt.read_text(encoding="utf-8-sig", errors="replace")

    media = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS),
                   key=lambda p: (not p.name.startswith("audio."), p.name))
    if not media:
        raise RuntimeError("未找到字幕或音频文件")
    if os.getenv("REMOTE_TRANSCRIBE_HOST", DEFAULT_REMOTE_HOST).strip():
        say("转录", "正在使用远程 VideoSrtToolkit 转录音轨")
        try:
            srt = _remote_transcript(media[0], folder)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            say("转录", f"远程转录失败，改用本地 faster-whisper：{exc}", "yellow")
            srt = _local_transcript(media[0], folder)
    else:
        say("转录", "正在使用本地 faster-whisper 转录音轨")
        srt = _local_transcript(media[0], folder)
    return srt, srt.read_text(encoding="utf-8", errors="replace")
