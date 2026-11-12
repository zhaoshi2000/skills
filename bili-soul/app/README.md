# BiliSoul

BiliSoul 从 B 站首页推荐或指定视频读取字幕与公开评论，结合模型生成视频分析和待审核的评论草稿。图形界面显示进度、日志和结果，并提供启动、暂停/继续、停止、关闭。分析结果保存在本机；主程序不会自动发布评论或执行互动。

## 安装（Windows）

需要 Python 3.10+。在此目录双击 `启动-Windows.bat`，或用 PowerShell 执行：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe main.py init
```

编辑 `.env`，填写自己的 `AI_BASE_URL`、`AI_API_KEY` 和 `AI_MODEL`。接口须兼容 OpenAI Chat Completions。`.env`、Cookie 和浏览器会话只保存在本机。

## 图形界面与命令行

双击 `启动图形界面.bat` 打开窗口。可留空视频输入框读取首页推荐，或输入 BV 号/视频链接分析指定视频。暂停与停止在当前网络、下载、转录或模型调用结束后的检查点生效；关闭窗口会先停止任务并等待远端临时文件清理。

```powershell
.venv\Scripts\python.exe main.py run --url BVxxxxxxxxxx
.venv\Scripts\python.exe main.py run
.venv\Scripts\python.exe main.py queue
```

`run` 会打开浏览器读取首页推荐；未登录时可先尝试匿名模式。需要登录时运行 `.venv\Scripts\python.exe main.py login`，在打开的浏览器中手动登录。浏览器会话保存在 `data/browser_profile/`。若没有 Chrome，Playwright 会使用已安装的 Chromium。

首页模式每次最多分析 `MAX_VIDEOS_PER_RUN` 条；默认跳过超过 `MAX_VIDEO_DURATION_SEC=900` 秒的视频。指定 BV 视频不受时长上限约束。`config/settings.json` 控制其他运行选项。

## 兴趣与表达设置

程序使用 `config/persona.example.json` 中的通用示例。若要自定义，将其复制为 `config/persona.json` 并编辑兴趣权重、表达风格和原则。个人设置文件已被 Git 忽略。

## 字幕与远程转录

程序优先提取视频已有字幕；没有字幕时下载音轨并尝试转录。若已配置可免交互 SSH 登录的 CPU 服务器，在 `.env` 中设置 `REMOTE_TRANSCRIBE_HOST` 和远端绝对路径 `REMOTE_TRANSCRIBE_TOOLKIT_DIR`，音轨会传到远端临时目录，转录后取回 SRT 并清理。未配置远端或远端不可用时，使用本机 faster-whisper。`WHISPER_MODEL` 可指定转录模型。

如需登录态才能获取的视频或字幕，可把浏览器导出的 B 站 Cookie JSON 放在 `data/bilibili-cookies.json`，或把 Netscape 格式放在 `data/cookies.txt`；两者同时存在时优先 JSON。只接受 `bilibili.com` 域名。程序不会读取系统浏览器 Cookie。

## 视频思维导图与笔记

仓库中的 [video-mindmap-note](../../video-mindmap-note/SKILL.md) 技能可将带时间戳的 SRT 整理为分层笔记和 JSON 大纲，使用其 `scripts/render_mindmap.py` 生成 SVG/PNG 思维导图。图可作为 B 站视频笔记的配图。

公开笔记涉及图片上传、私人保存、提交审核和状态回读，是与分析主程序分开的显式操作。先准备 UTF-8 正文文件与可选导图图片，再依次运行：

```powershell
.venv\Scripts\python.exe video_note.py save BVxxxxxxxxxx --title "笔记标题" --text-file note.txt --image mindmap.png
.venv\Scripts\python.exe video_note.py publish BVxxxxxxxxxx
.venv\Scripts\python.exe video_note.py verify BVxxxxxxxxxx
```

`--image` 可省略。Cookie 文件默认从 `data/` 读取，也可使用 `--cookies` 指定。`save` 先保存私人笔记并回读；`publish` 显式提交公开审核，且不会自动发评论；`verify` 查询审核状态与公开链接。每个 BV 号的状态保存在被 Git 忽略的 `data/`，防止重复提交。接口字段与验证结果见 [视频笔记接口](../references/video-note-api.md)。

## 运行数据

| 路径 | 内容 |
| --- | --- |
| `downloads/` | 下载的音轨及字幕 |
| `data/bilisoul.sqlite3` | 视频、评论样本、分析和草稿 |
| `data/browser_profile/` | 浏览器登录会话 |
| `logs/bilisoul.log` | 运行日志 |
| `config/persona.json` | 个人兴趣与表达设置（可选） |
| `.env` | 模型与转录配置 |

以上运行数据均不属于发布包。当前只抽取有限条按热度排序的公开一级评论，不能代表所有观众；自动转录也可能出错。下载和使用视频素材时遵守平台规则及版权要求。
