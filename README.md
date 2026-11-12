# Skills

每个根目录对应一个可独立安装的 Codex skill。复制所需目录到 Codex 的 `skills` 目录，然后重新加载技能。下列程序的运行配置和账号会话只保存在本机。

## bili-soul

[bili-soul](bili-soul/) 包含 BiliSoul 图形界面与命令行程序、视频笔记工具、B 站接口目录和对应的 `SKILL.md`。它读取视频字幕与公开评论，生成视频分析和待审核评论草稿。窗口可观察进度并启动、暂停、停止任务。主程序不自动执行账号互动。

需要 Python 3.10+；Windows 下进入 [app](bili-soul/app/) 后双击 `启动-Windows.bat` 初始化，再双击 `启动图形界面.bat`。首次运行按 [程序说明](bili-soul/app/README.md) 配置自己的模型接口与 B 站登录态。视频笔记发布是 [独立命令](bili-soul/app/video_note.py) 的显式操作。

## video-mindmap-note

[video-mindmap-note](video-mindmap-note/) 把带时间戳的字幕整理成笔记和思维导图大纲，并用附带脚本生成 SVG/PNG。可与 BiliSoul 的字幕和视频笔记流程配合使用，也可单独安装。

## douyin-web-api

[douyin-web-api](douyin-web-api/) 收录抖音网页登录态抓包、创作者中心第一方脚本定位的接口及官方开放平台 OpenAPI。目录区分实际请求、脚本静态确认和官方文档，并附可重复运行的脱敏抓包脚本。网页登录 Cookie 只在本机使用，不包含在仓库中。

## douyin-snapany-download

识别抖音与 B 站视频链接（包括 `v.douyin.com`、`bilibili.com` 和 `b23.tv`），通过 SnapAny 当前公开网页接口解析并下载公开视频。支持包含多个链接的分享文案。

B 站优先使用 FFmpeg 合并默认清晰度的视频和音频；若未安装 FFmpeg 或合并失败，仅在备用 MP4 同时包含视频和音轨时交付。抖音使用解析结果中的完整视频地址。程序不需要 HAR、浏览器 Cookie 或捕获的请求签名。

### 安装到 Codex

将 [douyin-snapany-download](douyin-snapany-download/) 目录复制或链接到 Codex 的 `skills` 目录，然后重新加载技能。

### 直接运行

需要 Python 3.10 或更新版本。FFmpeg 为可选依赖，用于合并 B 站高清分轨。

```bash
cd douyin-snapany-download
python scripts/download_douyin.py "https://www.bilibili.com/video/BV..."
python scripts/download_douyin.py "https://v.douyin.com/..." --output-dir ./downloads
```

下载文件默认保存到当前用户的 Downloads 目录。只处理可公开访问的视频；站点验证、额度限制或接口变化会导致下载失败。
