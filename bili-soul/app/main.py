import argparse, asyncio, json, os, re
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from bili_soul.logging import say
from bili_soul import db
from bili_soul.browser import login, get_feed
from bili_soul.bili_api import BiliAPIError, fetch_video_meta, fetch_comments
from bili_soul.media import download_video, transcript
from bili_soul.llm import analyze
from bili_soul.control import RunController, RunStopped

load_dotenv()
console = Console()
persona_path = Path("config/persona.json")
if not persona_path.exists():
    persona_path = Path("config/persona.example.json")
PERSONA = json.loads(persona_path.read_text(encoding="utf-8"))
SETTINGS = json.loads(Path("config/settings.json").read_text(encoding="utf-8"))

def interest_score(title):
    score = 0.05
    for category, weight in PERSONA.get("interests", {}).items():
        if category.lower() in title.lower():
            score += float(weight)
    terms = {
      "人工智能": ["AI", "大模型", "机器学习", "人工智能"],
      "科学技术": ["科学", "技术", "机器人", "无人机", "芯片"],
      "历史文化": ["历史", "考古", "文化"],
      "数码科技": ["手机", "电脑", "显卡", "数码"]
    }
    for category, words in terms.items():
        weight = PERSONA.get("interests", {}).get(category, 0)
        score += weight * sum(1 for word in words if word.lower() in title.lower())
    return min(score, 1.0)

def extract_bvid(value):
    match = re.search(r"BV[0-9A-Za-z]{10}", value)
    if not match:
        raise ValueError("请提供包含 BV 号的 B站视频链接或 BV 号")
    return match.group(0)


def _checkpoint(controller, stage, detail, **fields):
    if controller is not None:
        controller.checkpoint(stage, detail, **fields)


async def _run_impl(video_url=None, controller=None):
    if video_url:
        bvid = extract_bvid(video_url)
        feed = [{"bvid": bvid, "title": bvid,
                 "url": f"https://www.bilibili.com/video/{bvid}/"}]
        _checkpoint(controller, "指定视频", f"正在分析 {bvid}", bvid=bvid)
        say("指定视频", f"正在分析 {bvid}")
    else:
        _checkpoint(controller, "首页", "正在读取 B站首页推荐")
        say("首页", "正在读取B站首页推荐")
        feed = await get_feed(int(os.getenv("FEED_LIMIT", SETTINGS["feed_limit"])))
    if not feed:
        say("首页", "没有提取到视频，请确认已登录且首页正常加载", "red")
        return
    candidates = []
    for item in feed:
        if video_url or not db.seen(item["bvid"]):
            item["score"] = interest_score(item["title"])
            candidates.append(item)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    say("筛选", f"读取{len(feed)}条推荐，去重后{len(candidates)}条")
    count = 1 if video_url else int(os.getenv("MAX_VIDEOS_PER_RUN", SETTINGS["max_videos_per_run"]))
    max_duration = int(os.getenv("MAX_VIDEO_DURATION_SEC", "900"))
    selected = []
    for item in candidates:
        if len(selected) >= count:
            break
        _checkpoint(controller, "筛选", f"正在检查 {item['bvid']} 的时长", bvid=item["bvid"], title=item["title"])
        try:
            meta = fetch_video_meta(item["bvid"])
        except BiliAPIError as exc:
            if video_url:
                raise
            say("跳过", f"{item['bvid']} 元数据读取失败：{exc}", "yellow")
            continue
        if not video_url and max_duration > 0 and meta["duration"] > max_duration:
            say("跳过", f"{meta['title']}：时长超过 {max_duration} 秒", "yellow")
            continue
        selected.append((item, meta))
    for index, (item, meta) in enumerate(selected, 1):
        context = {"bvid": item["bvid"], "title": meta["title"]}
        _checkpoint(controller, "选择", f"{index}/{len(selected)} {meta['title']}", **context)
        say("选择", f"{index}/{len(selected)} {meta['title']}（兴趣分 {item['score']:.2f}）", "green")
        _checkpoint(controller, "评论", "正在读取评论区", **context)
        comment_sample = fetch_comments(meta["aid"], limit=30)
        comments = comment_sample["comments"]
        say("评论", f"已读取 {len(comments)} 条公开评论样本（评论总数约 {comment_sample['total']}）", "green")
        _checkpoint(controller, "字幕", "正在提取平台字幕或下载音轨", **context)
        folder = download_video(item["url"], item["bvid"])
        _checkpoint(controller, "转录", "正在读取或转录字幕", **context)
        srt, text = transcript(folder)
        say("字幕", f"字幕已保存：{srt}", "green")
        _checkpoint(controller, "理解", "正在结合字幕与评论调用模型", **context)
        say("理解", "正在结合字幕与评论调用模型分析视频")
        result = analyze(PERSONA, meta["title"], meta["description"], text,
                         comments, comment_sample["total"],
                         "自动语音转录" if srt.name == "transcript.srt" else "平台字幕")
        _checkpoint(controller, "保存", "正在保存分析与待审核草稿", **context)
        if controller is None:
            console.print(Panel(json.dumps(result, ensure_ascii=False, indent=2),
                                title="AI视频分析与评论草稿", border_style="cyan"))
        model_score = result.get("interest_score")
        score = float(model_score) if isinstance(model_score, (int, float)) and 0 <= model_score <= 1 else item["score"]
        db.save_video({"bvid": item["bvid"], "title": meta["title"], "url": item["url"],
                       "transcript_path": str(srt), "analysis": json.dumps(result, ensure_ascii=False),
                       "comments_json": json.dumps(comment_sample, ensure_ascii=False), "score": score})
        db.add_draft(item["bvid"], "video_comment", "", result["draft_comment"])
        if controller is not None:
            controller.emit("analysis", **context, result=result,
                            comment_count=len(comments), transcript_path=str(srt))
        say("记录", f"已保存视频、字幕、分析和评论草稿：{item['bvid']}", "green")
        say("互动", "公开评论、回复、点赞、投币、收藏均需人工确认；本版不会自动提交", "yellow")
    _checkpoint(controller, "结束", "本次运行即将完成")


async def run(video_url=None, controller: RunController | None = None):
    try:
        if controller is not None:
            controller.start()
        await _run_impl(video_url, controller)
    except RunStopped:
        if controller is not None:
            controller.stopped()
        say("停止", "本次运行已停止", "yellow")
    except Exception as exc:
        if controller is not None:
            controller.fail(str(exc))
        raise
    else:
        if controller is not None:
            controller.complete()

def queue():
    c = db.connect()
    rows = c.execute("SELECT id,bvid,kind,status,body FROM drafts ORDER BY id DESC").fetchall()
    c.close()
    if not rows:
        say("审核", "暂无草稿", "yellow")
        return
    for row in rows:
        console.print(Panel(row["body"], title=f"草稿 #{row['id']} | {row['bvid']} | {row['kind']} | {row['status']}"))

def main():
    parser = argparse.ArgumentParser(description="BiliSoul B站兴趣探索Agent")
    parser.add_argument("command", choices=["init", "login", "run", "queue"])
    parser.add_argument("--url", help="run 时可直接指定 B站视频链接或 BV 号")
    args = parser.parse_args()
    console.print(Panel.fit("[bold cyan]BiliSoul[/bold cyan] — B站自主兴趣探索 Agent"))
    if args.command == "init":
        db.connect().close()
        say("初始化", "数据库初始化完成。下一步编辑 .env；可复制 config/persona.example.json 到 config/persona.json 自定义偏好", "green")
    elif args.command == "login":
        asyncio.run(login())
    elif args.command == "run":
        asyncio.run(run(args.url))
    elif args.command == "queue":
        queue()

if __name__ == "__main__":
    main()
