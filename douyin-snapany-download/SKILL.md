---
name: douyin-snapany-download
description: 当用户消息含抖音或 B站视频链接（douyin.com、bilibili.com、b23.tv）时，通过 SnapAny 网页接口下载完整视频；不用于其他站点。
---

# 抖音与 B站视频下载

用户提供抖音或 B站视频链接时，运行脚本下载。它接受包含多个链接的分享文案，每个成功下载的视频输出一个保存路径。图文内容没有视频可下载，应明确告知。

```powershell
python scripts/download_douyin.py '<抖音或 B站链接或分享文案>'
```

从技能目录运行，或使用脚本绝对路径。用户指定保存目录时传 `--output-dir`；否则保存到当前用户的 Downloads 目录。回复保存路径，不要输出 SnapAny 媒体地址或带签名的请求头。

脚本沿用 HAR 中的 SnapAny 网页流程：读取当前公开前端脚本，在内存生成网页请求签名，调用解析接口，再按媒体专用请求头下载。不需要 HAR Cookie 或捕获的签名。B站优先用本机 `ffmpeg` 合并默认清晰度的视频与音频分轨；若分轨失败或没有 `ffmpeg`，仅在备用 MP4 经检查确实同时含视频和音轨时交付，否则应说明原因，必要时提示安装 `ffmpeg`。如果 SnapAny 返回 `free_limit_exceeded`，告知免费解析额度已耗尽并停止重试。若网页签名流程或接口改变，检查当前网页流程后再更新脚本，不要硬编码捕获的签名或把凭据放进技能。
