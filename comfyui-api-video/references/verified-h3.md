# 一次已验证的 MiniMax H3 API 链路

以下记录来自一台 ComfyUI 0.43.0、约 20 GB VRAM 的 RTX 3080 服务器，曾成功生成多个短镜头。它是工作流参考，不保证其他服务器、模型版本或种子有相同结果。运行前以 `/object_info`、模型列表和实际队列为准。

- 已用模型：`minimax_h3_ref2va_pruned_int8_convrot.safetensors`、`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`、`minimax_h3_video_vae_fp16.safetensors`。
- 视频链：`LoadImage` → `MiniMaxH3ReferenceToVideo`；模型由 `UNETLoader`、`CLIPLoader`、`VAELoader` 提供；条件与潜空间进入 `BasicGuider` / `SamplerCustomAdvanced`，再经 `VAEDecode` → `CreateVideo` → `SaveVideo`。
- 采样曾用 `KSamplerSelect(res_multistep)`、`BasicScheduler(simple, 20 steps)` 和 `RandomNoise`。单镜基线为 736×1312、124 帧、24 fps、`ref_image_size=match`，约 5.17 秒。一次三镜组合得到约 14 秒片段；不是模型单次生成 14 秒。
- `MiniMaxH3ReferenceToVideo` 的动态参考图 API 键曾是 `ref_images.ref_image_0`、`ref_images.ref_image_1` 等，实际名称须按当前 `/object_info` 核实。
- 这台服务器一次镜头可能耗时约 20 分钟。WebSocket `progress` 走完采样后，VAE 解码和 `SaveVideo` 仍需时间；界面 0% 或步骤已走完均不代表可以重交。
- 若需要修复人物换位或脸部漂移，可先生成位置正确的首帧，再用 `MiniMaxH3AddGuide(frame_idx=0)` 作锚点，同时减少同镜头内的复杂走位。曾有一个 768×1344、124 帧、20 步的镜头在半秒抽帧检查中未再看到换位；其他镜头仍需逐段检查。
- 1088×1920、124 帧、20 步的一次试验在约 12 分钟仍未完成第一步采样，任务随后被中断。因此这台服务器的原生竖屏 1080P 能力未得到验证。另行放大的 1080×1920 成品应标注为放大版。
- 曾有一次图片请求返回 429，另一次高质量首帧请求成功；这些只说明当时的请求结果，不代表图片服务永久不可用或无额度限制。
- 旧 MP4 因为只把视频帧接到 `CreateVideo.images` 而没有音频链，实际没有音轨。服务器当时列出 `minimax_h3_audio_vae_fp32.safetensors`、`VAEDecodeAudio` 和 `CreateVideo.audio`，但音频支路未实测，不能宣称能稳定产生指定台词。

要复用这条路线，先导出当前服务器可执行的 API 图，替换素材、提示词、模型名和输出位置，再用一个短镜头验证。

