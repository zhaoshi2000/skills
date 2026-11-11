# Skills

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
