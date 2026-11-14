"""Small ComfyUI API client for reference video workflows."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


def request(server, path, data=None, content_type=None, timeout=30):
    headers = {"Content-Type": content_type} if content_type else {}
    req = urllib.request.Request(server.rstrip("/") + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def read_json(server, path):
    return json.loads(request(server, path))


def print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def inspect(args):
    stats = read_json(args.server, "/system_stats")
    queue = read_json(args.server, "/queue")
    info = read_json(args.server, "/object_info")
    nodes = {name: info.get(name) for name in args.node} if args.node else sorted(info)
    print_json({"system_stats": stats, "queue": queue, "nodes": nodes})


def upload(args):
    path = Path(args.file)
    boundary = uuid.uuid4().hex
    name = path.name.replace('"', "")
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    result = json.loads(request(args.server, "/upload/image", body, f"multipart/form-data; boundary={boundary}", 120))
    print_json(result)


def submit(args):
    graph = json.loads(Path(args.workflow).read_text(encoding="utf-8"))
    if "prompt" in graph and isinstance(graph["prompt"], dict):
        graph = graph["prompt"]
    payload = json.dumps({"prompt": graph, "client_id": str(uuid.uuid4())}).encode()
    result = json.loads(request(args.server, "/prompt", payload, "application/json", 120))
    print_json(result)
    if not result.get("prompt_id"):
        raise ValueError("ComfyUI did not return prompt_id; inspect the response before retrying")


def get_history(server, prompt_id):
    return read_json(server, "/history/" + urllib.parse.quote(prompt_id, safe="")).get(prompt_id)


def wait(args):
    deadline = time.monotonic() + args.timeout
    last_state = None
    while True:
        history = get_history(args.server, args.prompt_id)
        if history:
            print_json({"prompt_id": args.prompt_id, "status": history.get("status"), "outputs": list(history.get("outputs", {}))})
            return 0 if history.get("status", {}).get("status_str") == "success" else 1
        queue = read_json(args.server, "/queue")
        running = any(item[1] == args.prompt_id for item in queue.get("queue_running", []))
        pending = any(item[1] == args.prompt_id for item in queue.get("queue_pending", []))
        state = "running" if running else "pending" if pending else "unknown"
        if state != last_state:
            print_json({"prompt_id": args.prompt_id, "state": state})
            last_state = state
        if time.monotonic() >= deadline:
            print_json({"prompt_id": args.prompt_id, "state": state, "message": "Timed out; check this prompt_id before any resubmission"})
            return 2
        time.sleep(args.interval)


def download(args):
    history = get_history(args.server, args.prompt_id)
    if not history or history.get("status", {}).get("status_str") != "success":
        raise ValueError("Prompt has no confirmed successful history")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for node_id, output in history.get("outputs", {}).items():
        if args.node and node_id not in args.node:
            continue
        for key in ("images", "gifs", "videos"):
            for item in output.get(key, []):
                filename = item.get("filename", "")
                if Path(filename).suffix.lower() not in (".mp4", ".webm", ".mov", ".mkv", ".gif"):
                    continue
                params = urllib.parse.urlencode({"filename": filename, "subfolder": item.get("subfolder", ""), "type": item.get("type", "output")})
                destination = output_dir / f"{args.prompt_id[:8]}_{node_id}_{Path(filename).name}"
                destination.write_bytes(request(args.server, "/view?" + params, timeout=300))
                saved.append(str(destination.resolve()))
    print_json({"prompt_id": args.prompt_id, "files": saved})
    return 0 if saved else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True, help="ComfyUI base URL, e.g. http://127.0.0.1:8188")
    commands = parser.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("inspect", help="Check server, queue and node schemas")
    probe.add_argument("--node", action="append", default=[], help="Node name to inspect; repeat as needed")
    uploading = commands.add_parser("upload", help="Upload one reference image")
    uploading.add_argument("file")
    submitting = commands.add_parser("submit", help="Submit an API-format prompt graph once")
    submitting.add_argument("workflow")
    waiting = commands.add_parser("wait", help="Wait for an existing prompt ID")
    waiting.add_argument("prompt_id")
    waiting.add_argument("--timeout", type=int, default=3600)
    waiting.add_argument("--interval", type=int, default=5)
    downloading = commands.add_parser("download", help="Download video outputs from successful history")
    downloading.add_argument("prompt_id")
    downloading.add_argument("--output-dir", required=True)
    downloading.add_argument("--node", action="append", default=[])
    args = parser.parse_args()
    try:
        return {"inspect": inspect, "upload": upload, "submit": submit, "wait": wait, "download": download}[args.command](args) or 0
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

