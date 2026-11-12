# 抖音全站接口目录（网页与开放平台）

整理日期：2026-11-12（北京时间）。本目录以用户授权的登录态网页浏览、抖音第一方创作者脚本和抖音开放平台官方文档为证据。网页抓包观察到 157 条去重路由；创作者脚本另定位 108 条路由（其中 97 条有可判定的方法）；开放平台文档补录约 45 条。各集合可能重叠，不应相加当作独立接口总数。

## 证据等级与使用边界

| 标记 | 含义 |
| --- | --- |
| 网页实测 | 登录浏览器确实发出请求，记录 HTTP 和可解析的业务码；不代表其他账号或之后仍可用 |
| 脚本静态 | 第一方页面加载的 JS 中定位到路径或方法；未代表账号执行成功 |
| 官方文档 | 抖音开放平台文档说明路径、权限和参数；本次未申请 OAuth 权限或调用 |

网页 Cookie 与开放平台 OAuth `access-token` 不互通。本文不含 Cookie 值、签名值、账号标识、响应正文或原始 HAR。初始页面导航抓包未主动发布、点赞、关注、评论、私信或删除内容；随后单独进行了一次图文发评尝试，结果见下文。

## 登录态网页实际抓包

抓取日期：2026-11-12（北京时间）。此文记录浏览器实际发出的 XHR/fetch 请求；不包含 Cookie、请求参数值、响应正文、签名值、账号 ID 或原始 HAR。

共访问 17 个页面场景，观察 766 次请求，按主机 + 方法 + 路径去重为 **157 条**。本人主页接口 `/aweme/v1/web/user/profile/self/` 返回 HTTP 200、业务码 0，登录态已确认。搜索页进入验证码中间页，因此不能据此宣称搜索结果接口已验证。

### 读表说明

- **验证** 表示这次浏览器观察到的结果。HTTP 200、业务码 0 表示该请求在当前会话成功；没有业务码的请求不能推断业务成功。页面自动发出的 POST 包括读取、心跳及状态更新，不能仅凭方法判断是否为发布操作。
- 参数列只列各路由的**业务差异字段**。网页通用环境、设备和签名字段见下一节；完整的参数**名称**另存于 `douyin_network.json`。字段名称和接口可随抖音版本变化。
- 上方 157 条路由统计来自页面导航抓包，当时未主动发评论、点赞、关注、投稿或私信。之后单独进行的图文发评尝试另列，不计入该统计。

### 网页共用参数

常见字段（并非每条都必需）：`a_bogus`, `aid`, `browser_language`, `browser_name`, `browser_online`, `browser_platform`, `browser_version`, `channel`, `cookie_enabled`, `cpu_core_num`, `device_memory`, `device_platform`, `downlink`, `effective_type`, `engine_name`, `engine_version`, `fp`, `msToken`, `os_name`, `os_version`, `pc_client_type`, `pc_libra_divert`, `platform`, `round_trip_time`, `screen_height`, `screen_width`, `support_dash`, `support_h265`, `uifid`, `update_version_code`, `verifyFp`, `version_code`, `version_name`, `webid`。`a_bogus`、`msToken` 等签名或会话字段只记录名称；不要复用旧值。

### 页面场景

| 场景 | 页面结果 |
| --- | --- |
| 精选首页 | 页面已加载 |
| 搜索（验证码） | 验证码中间页 |
| 关注流 | 页面已加载 |
| 本人收藏 | 页面已加载 |
| 消息 | 页面已加载 |
| 直播 | 页面已加载 |
| 创作者首页 | 页面已加载 |
| 投稿页 | 页面已加载 |
| 本人作品 | 页面已加载 |
| 本人喜欢 | 页面已加载 |
| 本人收藏集 | 页面已加载 |
| 发现 | 页面已加载 |
| 热点 | 页面已加载 |
| 作品管理 | 页面已加载 |
| 创作数据 | 页面已加载 |
| 他人主页 | 页面已加载 |
| 视频页 | 页面已加载 |

### 视频、推荐、搜索与播放（27 条）

| 主机 | 方法 | 路径 | 差异查询字段 | 请求体字段 | 场景 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| `www.douyin.com` | GET | `/aweme/v1/creator/external/highlight/` | highlight_type | — | 发现, 关注流, 精选首页, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/api/suggest_words/` | business_id, from_group_id, penetrate_params, rsp_source | — | 视频页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | GET | `/aweme/v1/web/app/installed/` | — | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/aweme/detail/` | aweme_id, origin_type, request_source, timestamp, x-secsdk-web-signature | — | 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v1/web/aweme/listcollection/` | publish_video_strategy_type, timestamp, x-secsdk-web-signature | count, cursor | 本人收藏 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/aweme/post/` | count, cut_version, from_user_page, locate_query, max_cursor, need_time_list, publish_video_strategy_type, sec_user_id, show_live_replay_strategy, time_list_query, timestamp, x-secsdk-web-signature | — | 本人收藏集, 本人作品, 他人主页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/aweme/related/` | Seo-Flag, awemePcRecRawData, aweme_id, count, refresh_index, sub_channel_id | — | 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/channel/hotspot` | Seo-Flag, channel_id, count, webcast_sdk_version, webcast_version_code | — | 热点 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/creator/overview/dashboard/` | recent_days | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/custom/settings/get/` | setting_types | — | 关注流, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/danmaku/conf/get/` | conf_end_type, hardware_concurrency | — | 关注流, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/danmaku/get_v2/` | app_name, authentication_token, duration, end_time, format, group_id, item_id, start_time | — | 关注流, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/douyin/select/study/ai_assistant/note/list` | count, filter_draft, offset | — | 本人收藏, 本人收藏集, 本人喜欢, 本人作品 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/douyin/select/tab/course/catagory/tag/` | tab_id | — | 发现, 精选首页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/emoji/list` | need_all, publish_video_strategy_type | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v1/web/history/write/` | — | author_id, aweme_id | 关注流, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/hot/search/list/` | detail_list, main_billboard_count, source, webcast_sdk_version, webcast_version_code | — | 发现, 关注流, 精选首页, 热点, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/mix/listcollection/` | count, cursor, timestamp, x-secsdk-web-signature | — | 发现, 关注流, 精选首页, 热点, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/mobile/ab/params/` | — | — | 关注流, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/multicast/query/` | — | — | 发现, 本人收藏, 关注流, 精选首页, 热点, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v1/web/page/turn/offline` | — | — | 发现, 本人收藏, 关注流, 精选首页, 热点, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v1/web/profile/record/` | publish_video_strategy_type | record_params, scene | 他人主页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/query/account/type/` | sec_uid | — | 关注流, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/seo/inner/link/` | — | — | 本人收藏, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/solution/resource/list/` | app_id, spot_keys | — | 发现, 精选首页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v2/web/aweme/stats/` | — | aweme_type, item_id, play_delta, source | 关注流, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v2/web/module/feed/` | Seo-Flag, awemePcRecRawData, count, install_time, is_active_tab, module_id, pre_item_from, pre_item_ids, pull_type, refer_type, refresh_index, use_lite_type, xigua_user | encoded_pre_item_ids | 发现, 精选首页 | HTTP 200，业务 0 |

### 评论（1 条）

| 主机 | 方法 | 路径 | 差异查询字段 | 请求体字段 | 场景 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| `www.douyin.com` | GET | `/aweme/v1/web/comment/list/` | aweme_id, count, cursor, cut_version, item_type | — | 视频页 | HTTP 200，业务 0 |

#### 后续图文发评尝试（不计入上方 157 条）

2026-11-12，在已登录的浏览器打开[图文作品](https://www.douyin.com/note/7703778454097557331)，通过页面编辑器点击发送一次，实际观察到 `POST https://www.douyin.com/aweme/v1/web/comment/publish`。请求体字段名：`aweme_id`、`comment_send_celltime`、`comment_video_celltime`、`one_level_comment_rank`、`paste_edit_method`、`text`、`text_extra`；查询字段名包括 `a_bogus`、`msToken`、`enter_from`、`previous_page`、`uid`。这里只记录字段名，不含参数值和评论正文。

该请求返回 **HTTP 403**，未取得可解析的业务码或评论 ID；页面编辑器仍保留草稿，评论数未变化。因此只确认此页面发出了上述 **POST 路由与字段结构**，不能确认发评成功，也不能推断账号在其他浏览器或之后能使用该接口。此次仅点击发送一次，未重复提交。

### 账号、关注与收藏（11 条）

| 主机 | 方法 | 路径 | 差异查询字段 | 请求体字段 | 场景 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| `www.douyin.com` | GET | `/aweme/v1/following/list/item/seen/` | item_id_list, type | — | 关注流 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/aweme/favorite/` | count, cut_version, max_cursor, min_cursor, publish_video_strategy_type, sec_user_id, timestamp, x-secsdk-web-signature | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/follow/feed/` | count, cursor, level, pull_type, webcast_sdk_version, webcast_version_code | — | 关注流 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/get/user/settings/` | — | — | 发现, 本人收藏, 关注流, 精选首页, 热点, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/query/user/` | publish_video_strategy_type | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/social/count` | source | — | 创作者首页, 发现, 本人收藏, 关注流, 精选首页, 热点, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/user/dashboard` | UserId, publish_video_strategy_type, webcast_sdk_version, webcast_version_code | — | 本人收藏, 本人收藏集, 本人喜欢, 本人作品, 视频页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | GET | `/aweme/v1/web/user/following/list/` | address_book_access, count, gps_access, is_top, max_time, min_time, offset, sec_user_id, source_type, user_id, webcast_sdk_version, webcast_version_code | — | 关注流 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/user/profile/other/` | land_to, personal_center_strategy, profile_other_record_enable, publish_video_strategy_type, sec_user_id, source | — | 他人主页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/user/profile/self/` | — | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/user/settings/` | has_local_cache, is_fetch_frequency_control, request_source | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |

### 消息、私信与通知（14 条）

| 主机 | 方法 | 路径 | 差异查询字段 | 请求体字段 | 场景 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| `imapi.douyin.com` | POST | `/v1/message/get_message_by_init` | — | <opaque-body> | 创作者首页, 创作数据, 作品管理, 投稿页, 发现, 本人收藏, 关注流, 精选首页, 搜索（验证码）, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务码未解析 |
| `imapi.douyin.com` | POST | `/v1/message/get_user_message` | — | <opaque-body> | 创作数据, 作品管理, 发现, 本人收藏, 搜索（验证码）, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务码未解析 |
| `imapi.douyin.com` | POST | `/v1/stranger/get_conversation_list` | — | <opaque-body> | 创作数据, 发现, 本人收藏, 消息, 搜索（验证码）, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | GET | `/aweme/v1/web/external/notification/` | client_type, os, scene, user_id | — | 发现, 关注流, 精选首页, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v1/web/im/get/online_feedback/entrance/` | app_id, entrance, publish_video_strategy_type | — | 发现, 关注流, 精选首页, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/im/resource/list/aggregation/` | app_id, custom_cursor, custom_limit, scenes, source | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/im/resources/emoticon/trending` | count, cursor, groupId | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/im/spotlight/relation/` | count, max_time, min_time, need_remove_share_panel, need_sorted_info, source, with_fstatus | — | 发现, 本人收藏集, 本人喜欢, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/im/strategy/config` | app_id, scenes | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/im/user/active/config/get` | — | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v1/web/im/user/active/status/` | — | conv_ids, sec_user_ids, source | 发现, 本人收藏集, 本人喜欢, 他人主页, 视频页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | GET | `/aweme/v1/web/im/user/active/update/` | action, new_user_login | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/aweme/v1/web/im/user/info/` | — | sec_user_ids | 发现, 本人收藏, 热点, 本人收藏集, 本人喜欢, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/aweme/v1/web/notice/count/` | is_new_notice, need_social_count | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |

### 直播（18 条）

| 主机 | 方法 | 路径 | 差异查询字段 | 请求体字段 | 场景 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| `baike.douyin.com` | GET | `/webcast/ip/wiki/check_worldbook_access` | webcast_sdk_version, webcast_version_code | — | 本人收藏, 本人收藏集, 本人喜欢, 本人作品, 他人主页 | HTTP 200，业务 0 |
| `baike.douyin.com` | GET | `/webcast/ip/wiki/get_account_binding_subject` | account_uid, webcast_sdk_version, webcast_version_code | — | 本人收藏, 本人收藏集, 本人喜欢, 本人作品, 他人主页 | HTTP 200，业务 0 |
| `live.douyin.com` | GET | `/aweme/v1/web/mix/listcollection/` | count, cursor | — | 创作者首页 | 请求未完成 |
| `live.douyin.com` | POST | `/aweme/v1/web/page/turn/offline` | — | — | 直播 | HTTP 200，业务 0 |
| `live.douyin.com` | GET | `/aweme/v1/web/seo/inner/link/` | — | — | 直播 | HTTP 200，业务 0 |
| `live.douyin.com` | GET | `/aweme/v1/web/user/appointment/list/` | app_name, appointment_type, count, enter_from, language, live_id, request_tag_from, scene | — | 直播 | HTTP 200，业务 0 |
| `live.douyin.com` | POST | `/passport/ticket_guard/get_client_cert/` | is_from_ttaccountsdk | server_data | 直播 | HTTP 200，业务码未解析 |
| `live.douyin.com` | GET | `/webcast/dress/list/` | live_id | — | 直播 | HTTP 200，业务 0 |
| `live.douyin.com` | GET | `/webcast/feed/` | action, action_type, app_name, custom_count, enter_from, enter_source, inner_from_drawer, is_draw, is_ssr, language, live_id, liveid, maxtime, need_map, request_tag_from, source_key | — | 直播 | HTTP 200，业务 0 |
| `live.douyin.com` | GET | `/webcast/feed/follow_top/` | app_name, enter_from, enter_source, follow_session_id, language, live_id, need_map, need_pinned_info, source_key, webcast_version_code | — | 直播 | HTTP 200，业务 0 |
| `live.douyin.com` | GET | `/webcast/room/info_by_scene/` | app_name, device_id, device_type, ignoreToast, language, live_id, region, room_id, scene, webcast_sdk_version | — | 发现 | HTTP 200，业务 0 |
| `live.douyin.com` | GET | `/webcast/setting/` | — | — | 发现, 本人收藏, 关注流, 精选首页, 热点, 直播, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `live.douyin.com` | HEAD | `/webcast/user/` | — | — | 直播 | HTTP 200，业务码未解析 |
| `live.douyin.com` | GET | `/webcast/user/me/` | app_name, enter_from, language, live_id, room_id | — | 直播 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/webcast/diamond/` | entrance, pc_entrance, type | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/webcast/feed/follow_top/` | — | enter_source, follow_session_id, need_map, need_pinned_info, source_key | 关注流 | HTTP 200，业务 0 |
| `www.douyin.com` | POST | `/webcast/moment/latest_replay/` | max_time, source, uid, version | — | 本人收藏, 本人收藏集, 本人喜欢, 本人作品 | HTTP 200，业务 0 |
| `www.douyin.com` | GET | `/webcast/web/feed/follow/` | scene | — | 本人收藏, 本人收藏集, 本人喜欢, 本人作品 | HTTP 200，业务 0 |

### 创作者中心与投稿（60 条）

| 主机 | 方法 | 路径 | 差异查询字段 | 请求体字段 | 场景 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| `creator.amemv.com` | POST | `/api/v1/workspace/feature_gates/values` | — | custom, is_header_added, user, workspace_name | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/account/api/v1/cert/roles` | — | — | 创作者首页 | HTTP 301 |
| `creator.douyin.com` | GET | `/account/api/v1/cert/roles/` | — | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/account/api/v1/user/account/info` | — | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/api/v2/douyin/charge/creator/offline_config/` | timezone_name | — | 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/api/v2/douyin/charge/permission/` | timezone_name, video_type | — | 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/api/v2/douyin/charge/recommend/config/` | timezone_name | — | 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/janus/creator/data/overview/all/` | last_days_type | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/mid/video/sts2/` | scene, timezone_name | — | 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/check/user/` | sec_uid | — | 作品管理 | 请求未完成 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/data/guide` | app_name, timezone_name, user_agent | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | POST | `/aweme/v1/creator/homepage/module` | app_name, timezone_name, user_agent | module_key_list, tpl_id | 创作者首页 | HTTP 307 |
| `creator.douyin.com` | POST | `/aweme/v1/creator/homepage/module/` | app_name, timezone_name, user_agent | <opaque-body> | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/im/user_token/` | app_name, timezone_name, user_agent | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/income/category/summary/` | app_name, timezone_name, user_agent | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/mission/user_summary` | app_name, history_day_count, timezone_name, user_agent | — | 创作者首页 | HTTP 301 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/mission/user_summary/` | app_name, history_day_count, timezone_name, user_agent | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/msg/top` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 301 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/msg/top/` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/notice/comment/` | app_name, timezone_name, user_agent | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/pc/user/info/` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/relation/following/list/` | app_name, count, cursor, timezone_name, user_agent | — | 创作数据 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/user/info/` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/user_message/list/` | app_name, count, cursor, timezone_name, type, user_agent | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/user_message/notice/` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/creator/user_message/unread_count/` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/web/douyin/select/hot/item/list/` | app_name, offset, size, timezone_name, type, user_agent | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/aweme/v1/web/oversea/judgment/` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/goofy/douyin_creator_pc/home/index.html` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | GET | `/goofy/douyin_creator_pc/mono/creator_content` | — | — | 作品管理, 投稿页 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | GET | `/goofy/douyin_creator_pc/mono/douyin_creator_data/` | — | — | 创作数据 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | GET | `/goofy/douyin_creator_pc/mono/prefetch/creator_content/manage/prefetch.json` | — | — | 作品管理 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | POST | `/goofy_worker/jwt` | — | — | 投稿页 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | GET | `/janus/douyin/creator/pc/work_list` | count, max_cursor, scene, status, timezone_name | — | 作品管理 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/live/api/anchor/get_create_info/` | timezone_name | — | 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | POST | `/passport/ticket_guard/get_client_cert/` | is_from_ttaccountsdk | server_data | 创作者首页 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | POST | `/passport/user_info/get_sec_ts/` | is_from_ttaccountsdk | aid, is_from_ttaccountsdk | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | POST | `/ttwid/check/` | — | aid, fid, migrate_priority, needFid, service, union, unionHost | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/center/ai_creation/entries` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/center/fans/index/config` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/center/starlight/balance` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/center/user/exclusive_operator` | app_id | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/center/user/relation_account` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/inspiration/activities/` | — | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/item/list` | count, end_time, fields, need_long_article, start_time, status_list[] | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/mcn/account_base_info` | show_mcn_status | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/creator/school/course` | is_hot, limit, offset, order | — | 创作者首页 | HTTP 301 |
| `creator.douyin.com` | GET | `/web/api/creator/school/course/` | is_hot, limit, offset, order | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | HEAD | `/web/api/media/anchor/search` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | POST | `/web/api/media/aweme/draft` | — | <opaque-body> | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | POST | `/web/api/media/aweme/draft/` | — | item | 创作者首页 | HTTP 307 |
| `creator.douyin.com` | GET | `/web/api/media/banner/info/` | timezone_name | — | 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/media/user/info/` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/mix/list/` | count, cursor, status, timezone_name | — | 作品管理 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/playlet/list/` | count, cursor, only_new_mix, status, timezone_name | — | 作品管理 | HTTP 200，业务 0 |
| `creator.douyin.com` | POST | `/web/api/v1/im/token/` | — | app_id, channel, is_visitor | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | GET | `/web/api/v2/creator/activity/pc/list` | end_time, start_time | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/v2/creator/activity/tags/query` | — | — | 创作者首页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/web/api/v2/creator/xigua/user/info` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务 0 |
| `creator.douyin.com` | GET | `/webcast/api/platform_following/outside/room/v1/live_status` | — | — | 创作者首页 | HTTP 200，业务 0 |

### 其他网页业务（4 条）

| 主机 | 方法 | 路径 | 差异查询字段 | 请求体字段 | 场景 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| `www.douyin.com` | GET | `/passport/general/login_guiding_strategy/` | account_app_language, account_sdk_source, account_sdk_source_info, biz_trace_id, is_from_ttaccountsdk, language, p_bd, p_js_t, p_js_v, p_no, p_ts, p_ver, p_ver_real, p_zt, passport_jssdk_type, passport_jssdk_version, qs, request_host, sign, ts | — | 精选首页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | POST | `/passport/ticket_guard/get_client_cert/` | is_from_ttaccountsdk | server_data | 精选首页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | POST | `/passport/user_info/get_sec_ts/` | is_from_ttaccountsdk | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | POST | `/ttwid/check/` | — | aid, service | 精选首页 | HTTP 200，业务 0 |

### 风控、埋点与前端资源（22 条）

| 主机 | 方法 | 路径 | 差异查询字段 | 请求体字段 | 场景 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| `creator.douyin.com` | GET | `/goofy/douyin_creator_pc/creator_pc_vmok_common/vmok-manifest.json` | — | — | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务码未解析 |
| `creator.douyin.com` | GET | `/goofy/douyin_creator_pc/vmok/author-tag/vmok-manifest.json` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/css/async/__federation_expose_author_tag.e7f4f436.css` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/css/lib-semi.d4b7814c.css` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/js/527.91760161.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/js/593.3880058e.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/js/async/__federation_expose_author_tag.6c33e085.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/js/lib-axios.7ee9e332.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/js/lib-lodash.9fb55755.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/js/lib-polyfill.51d2667e.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/js/lib-react.55c4fc4d.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/static/js/lib-semi.af88e932.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `lf-fe-douyin-account.amemv.com` | GET | `/obj/ies-douyin-account-fe/ies/douyin_creator_certification/vmok-remote-entry.2530b0cf.js` | — | — | 创作者首页 | HTTP 200，业务码未解析 |
| `mcs.snssdk.com` | POST | `/list` | — | <array> | 创作者首页, 创作数据, 作品管理, 投稿页, 本人作品, 他人主页 | HTTP 200，业务码未解析 |
| `mcs.snssdk.com` | POST | `/tobid` | — | app_id, user_unique_id, web_id | 创作者首页, 创作数据, 作品管理, 投稿页 | HTTP 200，业务码未解析 |
| `mcs.snssdk.com` | POST | `/webid` | — | app_id, referer, url, user_agent, user_unique_id | 创作者首页, 作品管理 | HTTP 200，业务码未解析 |
| `vcs.snssdk.com` | POST | `/vc/setting` | — | — | 搜索（验证码） | HTTP 200，业务码未解析 |
| `verify.snssdk.com` | POST | `/captcha/reportFrontend` | — | logs | 搜索（验证码） | HTTP 200，业务码未解析 |
| `www.douyin.com` | POST | `/cloudpush/update_sender/` | device_brand, device_model, device_type, os | aid, push_sdk | 精选首页, 他人主页, 视频页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | GET | `/pcim_saas_vmok_entry/vmok-manifest.json` | — | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | GET | `/recharge_web_vmok/vmok-manifest.json` | — | — | 发现, 本人收藏, 关注流, 精选首页, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务码未解析 |
| `www.douyin.com` | POST | `/service/2/abtest_config/` | — | header | 发现, 本人收藏, 关注流, 精选首页, 热点, 直播, 本人收藏集, 本人喜欢, 本人作品, 他人主页, 视频页 | HTTP 200，业务码未解析 |

### 边界与复查

此次是有限页面的网页端观察，不等于抖音所有业务接口。不同账号权限、地区、页面版本和验证码状态会改变请求。创作者中心、直播和私信可能使用独立域名或 Protobuf/WebSocket；上方 157 条清单只包括初始导航抓包的 XHR/fetch 路由。之后另有一次图文发评请求返回 HTTP 403；其他发布、删除、支付等写操作没有做实测。

## 创作者中心第一方脚本

时间：2026-11-12，北京时间。站点：[抖音创作者中心](https://creator.douyin.com/)。从 `creator.douyin.com` 首页加载的第一方 JS，及未登录的隔离浏览器访问创作、作品管理、评论和数据页面取得证据。所有页面访问均为只读；未投稿、删除、回复、置顶或修改账号。第一方脚本路径证据不等于实际调用成功。

### 关键结果

| 操作 | 方法与站内路径 | 参数与结论 | 证据 |
| --- | --- | --- | --- |
| 查询上传临时授权 | GET `/web/api/media/upload/auth/v5/` | 页面脚本读取 `auth` 和 `client_ip`；未在登录态实测 | [主 bundle](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-master-new/static/js/main.394140d5.js) |
| 查询上传配置 | GET `/web/api/media/upload/config` | 第一方代码 `method:"get"`；未在登录态实测 | [主 bundle](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-master-new/static/js/main.394140d5.js) |
| 保存草稿 | POST `/web/api/media/aweme/draft/` | 第一方代码中的请求体包含 `item.common.draft.req_type=3`；未执行写入 | [创作前端 chunk](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/128.47c0d02a.js) |
| 删除作品 | POST `/web/api/media/aweme/delete/` | 第一方代码发送 JSON，且标记 `needSign:true`；未执行写入 | [作品管理前端](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| 作品置顶 | POST `/web/api/media/item/top/` | 第一方作品管理代码；未执行写入 | [作品管理前端](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| 创作者回复评论 | POST `/aweme/v1/creator/comment/reply/` | 第一方请求字段 `comment_Id,item_id,text`；未执行写入 | [创作者前端 chunk](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| 评论通知 | GET `/aweme/v1/creator/notice/comment/` | 第一方请求；未在登录态实测 | [创作者前端 chunk](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| 作品列表 | GET `/web/api/creator/item/list` | 第一方代码带 `user_id,count,cursor,order_by,fields` 等 query 字段 | [数据中心前端](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-mono-pc-data/static/js/douyin_creator_data_old.5eeb59d0.js) |
| 单作品数据汇总 | GET `/web/api/creator/data/item/summarize` | 第一方代码带 `item_id` query 字段 | [数据中心前端](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-mono-pc-data/static/js/douyin_creator_data_old.5eeb59d0.js) |
| 视频处理状态 | GET `/web/api/media/video/transend/` | 第一方代码带 `video_id` query 字段 | [作品管理前端](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| 视频片段合成 | POST `/web/api/media/video/concat/` | 第一方代码发送 JSON；未执行写入 | [作品管理前端](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |

`/web/api/media/aweme/create`、`create_v2`、`update_v2`、`reedit`、`editor/compose/trigger` 在[主 bundle](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-master-new/static/js/main.394140d5.js)中只出现在路由字符串列表，不能凭该列表确认方法、字段、是否仍被页面调用。其他仅在脚本出现而无法确认方法的路径在下表写为“待确认”。

### 未登录页面请求

隔离浏览器访问首页、上传页、作品管理、评论数据、统计页时，实际发出 7 条创作者域名请求。下表只记录方法、路径、HTTP 与业务状态；状态码 8/4 显示需要登录或权限，本次不能据此认定登录态功能可用。

| 方法与路径 | HTTP | 业务码 |
| --- | --- | --- |
| GET `/aweme/v1/creator/pc/user/info/` | 200 | 8 |
| GET `/aweme/v1/creator/user/info/` | 200 | 8 |
| GET `/aweme/v1/web/oversea/judgment/` | 200 | 0 |
| GET `/web/api/creator/center/fans/index/config` | 200 | 4 |
| HEAD `/web/api/media/anchor/search` | 200 | 未返回 JSON 业务码 |
| GET `/web/api/media/user/info/` | 200 | 8 |
| GET `/web/api/v2/creator/xigua/user/info` | 200 | 8 |

### 路由证据说明

以下条目来自浏览器实际加载的第一方 `douyinstatic.com` JS。方法从相邻调用代码提取，未对账号写接口发请求。脚本中出现不等于页面已调用；需以已登录浏览器抓包进一步确认业务返回。

#### 投稿、素材与作品管理（21 条）
| 方法 | 路径 | 第一方脚本 |
| --- | --- | --- |
| GET | `/web/api/creator/item/mix/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/item/mix/list/download` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/item/mix/mget` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| POST | `/web/api/media/anchor/search/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| POST | `/web/api/media/aweme/delete/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| POST | `/web/api/media/aweme/draft/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/128.47c0d02a.js) |
| 待确认 | `/web/api/media/aweme/search/post` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-mono-pc-data/static/js/douyin_creator_data_old.5eeb59d0.js) |
| GET | `/web/api/media/aweme/search/post/auth` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/media/creator/anchor/get_product_list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/media/creator/book/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/media/csr/creator/proj/list/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/media/hashtag/activity/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| POST | `/web/api/media/item/top/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| POST | `/web/api/media/long_article/rights` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/128.47c0d02a.js) |
| GET | `/web/api/media/top/users` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/media/user/info/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| POST | `/web/api/media/video/concat/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/media/video/copy/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/media/video/transend/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/mix/list/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/playlet/list/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |

#### 评论与消息（7 条）
| 方法 | 路径 | 第一方脚本 |
| --- | --- | --- |
| POST | `/aweme/v1/creator/comment/reply/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/aweme/v1/creator/im/user_detail` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/notice/comment/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/aweme/v1/creator/notice/mark_read` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| 待确认 | `/aweme/v1/creator/user_message/batch_read/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/home.58586c8f.js) |
| 待确认 | `/aweme/v1/creator/user_message/list/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/home.58586c8f.js) |
| 待确认 | `/aweme/v1/creator/user_message/unread_count/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/home.58586c8f.js) |

#### 数据、作品与收益（12 条）
| 方法 | 路径 | 第一方脚本 |
| --- | --- | --- |
| POST | `/aweme/v1/creator/data/competing/add` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/aweme/v1/creator/data/competing/delete` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/data/guide` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/data/overview/billboard` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/data/overview/option` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/data/v2/billboard_list/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/income/category/summary/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/income/creator_share/xigua/trend` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/data/item/summarize` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-mono-pc-data/static/js/douyin_creator_data_old.5eeb59d0.js) |
| GET | `/web/api/creator/item/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-mono-pc-data/static/js/douyin_creator_data_old.5eeb59d0.js) |
| GET | `/web/api/creator/item/list/download` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/material/center/billboard` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |

#### 机构 / MCN（37 条）
| 方法 | 路径 | 第一方脚本 |
| --- | --- | --- |
| 待确认 | `/aweme/v1/creator/user/apply/mcn/rescission/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/home.58586c8f.js) |
| GET | `/web/api/creator/mcn/account_base_info` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/account_detail` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/announce` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/banner` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/base_info` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/config` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/feishu/info` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/feishu/state` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/feishu/state_status` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/feishu/unbind` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/item/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/item/manager/filters` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/logo/update` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/message/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/message/mark_read` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/message/unread_count` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/metric_trend` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/rank` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/register/order/create` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/register/order/guarantee_fee/check` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/register/stage/complete/invite_stage` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/register/stage/info` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/register/talent/add` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/register/talent/delete` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/star/apply` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/star_binding/create` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/star_binding/decision` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/star_binding/star_mcn` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/star_binding/state` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/summarize_data` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/talent/filters` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/talent/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/talent/rank` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/talent/relation` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/web/api/creator/mcn/talent/update_fav_status` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/mcn/top_talent` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |

#### 直播与挂载（9 条）
| 方法 | 路径 | 第一方脚本 |
| --- | --- | --- |
| POST | `/webcast/api/platform_following/outside/room/v1/live_status` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/128.47c0d02a.js) |
| POST | `/webcast/gamecp/anchor/start_promotion/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/webcast/gamecp/anchor/support_modes` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/webcast/gamecp/game/settlement_rule/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/webcast/gamecp/mount_page/game_list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/webcast/gamecp/mount_page/search` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/webcast/gamecp/page/set_status/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/webcast/gamecp/promotion/games/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| 待确认 | `/webcast/subscribe/get_privilege_info/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |

#### 其他创作者功能（22 条）
| 方法 | 路径 | 第一方脚本 |
| --- | --- | --- |
| GET | `/aweme/v1/creator/get/url/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| 待确认 | `/aweme/v1/creator/homepage/app/module/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/128.47c0d02a.js) |
| POST | `/aweme/v1/creator/homepage/module` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| 待确认 | `/aweme/v1/creator/mission/card/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/mission/message_list/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/mission/mine/card/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/aweme/v1/creator/mission/user_summary` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/aweme/v1/creator/permission/confer/edit/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| POST | `/aweme/v1/creator/role/apply` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-mono-pc-data/static/js/douyin_creator_data_old.5eeb59d0.js) |
| GET | `/aweme/v1/creator/search/user` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| 待确认 | `/aweme/v1/creator/upload/user/file/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/home.58586c8f.js) |
| GET | `/aweme/v1/creator/user/info` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/aweme/v1/creator/user/info/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/aweme/v1/creator/user/search/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/calendar/event/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/inspiration/activities/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/creator/school/course` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/medium/search/` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| 待确认 | `/web/api/safeguard/original/entertainment` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| 待确认 | `/web/api/safeguard/original/pre_checkinfo` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js) |
| GET | `/web/api/v2/creator/activity/pc/list` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |
| GET | `/web/api/v2/creator/activity/tags/query` | [JS](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/4059.78d171bc.js) |

### 创作者中心当前第一方脚本补充

在未登录的创作者中心页面 `https://creator.douyin.com/creator-micro/content/post/video` 加载的[内容模块脚本](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-content-new/micro/static/js/douyin_content_index_micro_new.26f8d732.js)中，以下路径与 `get`/`post` 请求调用直接相连。**等级：脚本静态确认方法，未触发对应业务请求**；参数体仍需实际业务页面核对。

| 方法、路径（`creator.douyin.com`） | 脚本中用途线索 |
| --- | --- |
| POST `/web/api/media/aweme/delete/` | 删除作品 |
| POST `/web/api/media/item/top/` | 置顶作品 |
| POST `/web/api/media/video/concat/` | 视频片段拼接 |
| POST `/web/api/media/anchor/search/` | 搜索投稿锚点 |
| GET `/web/api/media/aweme/search/post/auth` | 投稿前权限信息 |
| GET `/web/api/media/video/transend/` | 视频转码/传输完成状态；脚本参数含 `video_id` |
| GET `/web/api/media/hashtag/activity/` | 话题活动信息 |
| GET `/aweme/v1/creator/get/url/` | 媒体 URI 换可访问 URL；参数 `uri` |
| GET `/live/api/replay/get_replay_list/` | 直播回放列表 |
| POST `/live/api/replay/delete/` | 删除直播回放 |
| POST `/live/api/replay/setting_update/` | 更新直播回放设置 |
| POST `/live/api/replay/transcode/` | 回放转码 |

另一份创作者中心[主脚本](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-master-new/static/js/main.394140d5.js)明确构造了 `GET https://www.douyin.com/aweme/v1/web/im/spotlight/relation/` 和 `POST https://www.douyin.com/aweme/v1/web/im/user/info/`，都带 `withCredentials:true`。后者虽为 POST，但用途为读取联系人资料，不是发送私信。主脚本还包含 `POST /aweme/v1/creator/msg/read`（标记消息已读）和 `GET /aweme/v1/creator/msg/top` 的客户端方法。独立[消息模块脚本](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin_creator/fe/pc/static/js/message.2de2ec19.js)引用 `/aweme/v1/creator/user_message/list/`、`/unread_count/`、`/batch_read/`，但其封装方法未在此处解码，故不在此推断 HTTP 方法。

主脚本中的 `/web/api/media/aweme/create`、`/create_v2`、`/draft`、`/update_v2`、`/aweme/v1/creator/comment/reply`，及[共享脚本](https://lf-fe-creator.douyinstatic.com/obj/douyn-creator-scm-cdn/douyin-creator-master-new/static/js/805.42ac3bdb.js)中的 `/aweme/v1/web/commit/item/digg`、`/aweme/v1/web/commit/follow/user`，只出现在性能监控/埋点白名单字符串里；**不能据此当成已验证接口或推断方法与参数**。`/aweme/v1/web/comment/publish` 也在该白名单中，但后续图文发评尝试独立观察到了其 POST 方法和请求字段；该次返回 HTTP 403，并未证实发表成功。本次没有在可用第一方脚本里确认普通用户网页的点赞、收藏、关注或私信发送请求调用。

## 开放平台新版文档路径

抖音开放平台的 `open.douyin.com` OpenAPI 使用应用权限、用户 OAuth 授权与 `access-token`；浏览器导出的 `douyin.com` Cookie 不能代替这些凭据。下表全部是官方文档核对，并未调用账号接口。旧版文档有迁移提示，优先记录新版 `developer.open-douyin.com` 的路径。

| 业务 | 方法与官方路径 | 权限 / 关键参数 | 官方依据 |
| --- | --- | --- | --- |
| 换取用户令牌 | POST `https://open.douyin.com/oauth/access_token/` | OAuth 临时授权码、`client_key`、`client_secret`；Cookie 不能代替 | [获取 access_token](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/account-permission/get-access-token/) |
| 获取授权用户资料 | POST `/oauth/userinfo/` | `user_info`；`open_id`、`access_token` | [获取用户公开信息](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/account-permission/get-account-open-info) |
| 上传视频 | POST `https://open.douyin.com/api/douyin/v1/video/upload_video/` | `video.create.bind`；`open_id`、multipart `video`，返回 `video_id` | [上传视频](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/create-video/upload-video) |
| 分片初始化 | POST `/api/douyin/v1/video/init_video_part_upload/` | `video.create.bind`；`open_id`，返回 `upload_id` | [分片初始化](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/create-video/video-part-upload-init) |
| 分片上传 | POST `/api/douyin/v1/video/upload_video_part/` | `video.create.bind`；上传片段 | [分片上传](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/create-video/video-part-upload) |
| 分片完成 | POST `/api/douyin/v1/video/complete_video_part_upload/` | `video.create.bind`；汇总片段得到 `video_id` | [分片完成](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/create-video/video-part-upload-complete) |
| 创建视频 | POST `/api/douyin/v1/video/create_video/` | `video.create.bind`；`open_id`、`video_id`、`text` 等；提交后需审核 | [创建视频](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/create-video/video-create) |
| 上传图文图片 | POST `/api/douyin/v1/video/upload_image/` | `video.create.bind`；`open_id`、multipart `image`，返回 `image_id` | [图片上传](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/create-image-text/image-upload) |
| 发布图文（旧版路径） | POST `/image_text/create/` | `video.create`；图片上传后提交审核；旧站文档可能迁移 | [旧版发布图片文档](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/publish-img/publish/) |
| 查询视频基础信息 | POST `/api/douyin/v1/video/video_basic_info/` | `posting.behavior`，需要申请权限和用户授权 | [查询视频基础信息](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/posting-task/video-basic-info) |
| 读取评论（旧版路径） | GET `/item/comment/list/` | `item.comment`；应用权限、用户授权；公开作品 | [评论列表](https://open.douyin.com/platform/resource/docs/openapi/interaction-management/comment-management-user/comment-list) |
| 回复自己作品的评论（旧版路径） | POST `/item/comment/reply/` | `item.comment`；只支持获授权用户自己发布的视频 | [回复视频评论](https://open.douyin.com/platform/resource/docs/openapi/interaction-management/comment-management-user/video-comment-reply/) |
| 粉丝列表 | GET `/fans/list/` | `fans.list`；`open_id`、游标等 | [获取粉丝列表](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/account-management/user-data/get-fans-list) |
| 关注列表 | GET `/following/list/` | `following.list`；`open_id`、`count`、`cursor` | [获取关注列表](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/account-management/user-data/get-user-follow-list) |
| 互关列表 | GET `/friend/list/` | `friend.list`；`open_id`、`count`、`offset` | [获取双向关注](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/account-management/user-data/get-friend-list) |
| 视频搜索 | GET `/dy_open_api/v1/search/video/` | `aweme.dy.video_search`；`keyword`、`count`、`cursor`、`search_id` | [抖音视频搜索](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/douyin-search-capability/aweme-dy-video-search) |
| 图文搜索 | GET `/dy_open_api/v1/search/experience/` | `aweme.experience.search`；`keyword`、`count`、`content_type`、`cursor` | [抖音图文搜索](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/douyin-search-capability/aweme-experience-search) |
| 企业号主动私信 | 官方能力文档，具体接口随权限及消息类型区分 | `enterprise.im`；仅企业号，需申请权限和用户授权 | [企业私信接入方案](https://open.douyin.com/platform/resource/docs/ability/enterprise-account-open-ability/message-solution/) |

官方 [OpenAPI 列表](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/list) 另覆盖搜索、生活服务、电商及工具等业务；与网页内部接口属于不同接入体系，不应混用身份凭证或路径。

## 开放平台旧版文档索引

旧文档站有迁移提示，以下路径用于历史对照；接入时以新版官方文档及当前应用权限为准。

核对日期：2026-11-12。来源仅限 `open.douyin.com` 官方文档。本文件是给主接口目录合并的工作材料；以下路径均**有官方文档但未以本次用户账号实际调用**。官方开放平台 OpenAPI 与 `www.douyin.com` 网页内部接口是两套鉴权体系：前者需要开发者应用、相应 scope 和 OAuth `access_token`，浏览器 Cookie 不能直接代替。官方[术语说明](https://open.douyin.com/platform/resource/docs/common-question/words-explain/)和[权限表](https://open.douyin.com/platform/resource/docs/accession-guide/type-and-permission/)明确了这一点。部分单接口页面标注旧文档站自 2022 年 9 月起迁移，方法、路径和权限应在实际接入时重新核对。

### 授权与用户

| 方法、路径（基址 `https://open.douyin.com`） | 用途 / 关键字段 | 权限 | 第一方来源 |
| --- | --- | --- | --- |
| GET `/platform/oauth/connect/` | 向用户展示授权页并取得一次性 `code`；不是后台静默调用 | 申请所需 scope | [获取授权码](https://open.douyin.com/platform/resource/docs/openapi/account-permission/douyin-get-permission-code) |
| POST `/oauth/access_token/` | `code` 换 `access_token`、`refresh_token`、`open_id` | 已完成用户授权 | [获取 access token](https://open.douyin.com/platform/resource/docs/openapi/account-permission/get-access-token) |
| POST `/oauth/refresh_token/` | 刷新用户 `access_token` | 有效 refresh token | [刷新 access](https://open.douyin.com/platform/resource/docs/openapi/account-permission/refresh-access-token) |
| POST `/oauth/renew_refresh_token/` | 延长 refresh token；旧值随调用失效 | `renew_refresh_token` | [刷新 refresh token](https://open.douyin.com/platform/resource/docs/openapi/account-permission/refresh-token) |
| POST `/oauth/client_token/` | 应用级凭据，用于无需用户授权的能力 | `client_key`、`client_secret` | [生成 client_token](https://open.douyin.com/platform/resource/docs/openapi/account-permission/client-token) |
| POST `/oauth/userinfo/` | 公开昵称、头像、地区等；Body 为 `access_token`,`open_id` | `user_info` | [用户公开信息](https://open.douyin.com/platform/resource/docs/openapi/account-management/get-account-open-info) |
| GET `/following/list/` | 授权用户关注列表；`open_id`,`cursor`,`count` | `following.list` | [关注列表](https://open.douyin.com/platform/resource/docs/openapi/account-management/get-subscriber-list/) |
| GET `/fans/list/` | 授权用户粉丝列表 | `fans.list` | [粉丝列表](https://open.douyin.com/platform/resource/docs/openapi/account-management/get-fans-list) |
| GET `/fans/check/` | `follower_open_id` 是否关注 `open_id` | `fans.check` | [粉丝判断](https://open.douyin.com/platform/resource/docs/openapi/account-management/fans-judge) |

官方开放平台未在上述权限表中提供面向普通第三方的“关注/取消关注”“点赞/取消点赞”“收藏/取消收藏”写接口。`following.list`、视频点赞数据接口都是读取，不能当作写接口。

### 视频与图文投稿、内容管理

| 方法、路径 | 用途 / 关键字段 | 权限 | 第一方来源 |
| --- | --- | --- | --- |
| POST `/video/upload/` | multipart `video`，返回 `video_id`；单次上传适合较小视频 | `video.create` | [上传视频](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/upload) |
| POST `/video/part/init/` | 分片初始化，返回 `upload_id` | `video.create` | [初始化分片](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/slice-init-upload) |
| POST `/video/part/upload/` | 上传视频分片 | `video.create` | [分片上传](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/slice-upload/) |
| POST `/video/part/complete/` | `upload_id` 完成分片，返回 `video_id` | `video.create` | [完成分片](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/slice-accomplish-upload/) |
| POST `/video/create/` | 使用上传取得的 `video_id` 投稿；支持话题、@用户和指定锚点，投稿后须审核 | `video.create` | [创建视频](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video/) |
| POST `/image/upload/` | 上传图文图片，返回 `image_id` | `video.create` | [上传图片](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/publish-img/upload/) |
| POST `/image_text/create/` | Body `image_list`,`text`，可带 `at_users`、POI、小程序字段；投稿后须审核 | `video.create` | [发布图片](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/publish-img/publish/) |
| GET `/video/list/` | 授权账号投稿列表；`open_id`,`cursor`,`count` | `video.list` | [视频列表](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/search-video/account-video-list/) |
| POST `/video/data/` | Body `item_ids` 查询自己作品的实时播放与互动数据 | `video.data` | [视频数据](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/search-video/video-data/) |
| POST `/video/delete/` | Body `item_id` 删除自己视频，不可恢复 | `video.delete` | [删除视频](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/delete-video/delete/) |
| GET `/poi/search/keyword/` | 投稿地点关键词搜索 | `poi.search`；应用级 token | [查询 POI](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/search-video/video-poi) |

官方[内容发布接入方案](https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution/)说明开放平台发布需要相关权限，图片和视频存在审核。图片接口 `image_list` 使用图片上传得到的 ID，不是网页创作者中心的上传地址。官方接口不等同于网页用户在创作者中心的内部投稿请求。

### 评论与回复

| 方法、路径 | 用途 / 关键字段 | 权限与范围 | 第一方来源 |
| --- | --- | --- | --- |
| GET `/item/comment/list/` | 自己作品评论；`open_id`,`item_id`,`cursor`,`count`,`sort_type` | `item.comment`，用户授权 | [评论列表](https://open.douyin.com/platform/resource/docs/openapi/interaction-management/comment-management-user/comment-list) |
| GET `/item/comment/reply/list/` | 某评论回复；另需 `comment_id` | `item.comment`，用户授权 | [评论回复列表](https://open.douyin.com/platform/resource/docs/openapi/interaction-management/comment-management-user/comment-reply-list/) |
| POST `/item/comment/reply/` | Body `item_id`,`content`，回复某条再加 `comment_id` | `item.comment`；只能回复授权用户自己发布的视频 | [回复视频评论](https://open.douyin.com/platform/resource/docs/openapi/interaction-management/comment-management-user/video-comment-reply/) |
| GET `/video/comment/list/` | 企业号视频评论 | `video.comment`，企业号 | [企业评论列表](https://open.douyin.com/platform/resource/docs/openapi/enterprise-open-ability/comment-management-enterprise/comment-list/) |
| GET `/video/comment/reply/list/` | 企业号视频评论回复 | `video.comment`，企业号 | [企业评论接入方案](https://open.douyin.com/platform/resource/docs/ability/interaction-management/video-comment-management-solution/) |
| POST `/video/comment/reply/` | 企业号回复评论 | `video.comment`，企业号 | [企业回复评论](https://open.douyin.com/platform/resource/docs/openapi/enterprise-open-ability/comment-management-enterprise/video-comment-reply/) |
| POST `/video/comment/top/` | 企业号置顶评论 | `video.comment`，企业号 | [置顶评论](https://open.douyin.com/platform/resource/docs/openapi/enterprise-open-ability/comment-management-enterprise/top-video-comment/) |

开放平台普通账号回复接口限定自己的视频；不能据此推断存在给任意公开视频发一级评论的公开 OpenAPI。企业评论能力有申请范围与配额限制，以[官方接入方案](https://open.douyin.com/platform/resource/docs/ability/interaction-management/video-comment-management-solution/)为准。

### 搜索、热点

| 方法、路径 | 用途 | 权限 | 第一方来源 |
| --- | --- | --- | --- |
| GET `/video/search/` | 已审核关键词搜索近期公开视频；官方描述只返回最近一天 | `video.search` | [关键词视频搜索](https://open.douyin.com/platform/resource/docs/openapi/search-management/keywords-video-list/keywords-video/) |
| GET `/video/search/comment/list/` | 关键词命中视频的评论 | `video.search.comment` | [关键词评论](https://open.douyin.com/platform/resource/docs/openapi/search-management/keywords-video-comment-management/comment-list/) |
| GET `/video/search/comment/reply/list/` | 上述评论的回复 | `video.search.comment` | [关键词评论回复列表](https://open.douyin.com/platform/resource/docs/openapi/search-management/keywords-video-comment-management/comment-reply-list/) |
| POST `/video/search/comment/reply/` | 回复关键词视频下评论 | `video.search.comment` | [关键词评论回复](https://open.douyin.com/platform/resource/docs/openapi/search-management/keywords-video-comment-management/comment-reply/) |
| GET `/hotsearch/sentences/` | 实时热点词 | `hotsearch`，应用级 token | [热点词](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/hot-video-data/get-current-hot-words/) |
| GET `/hotsearch/trending/sentences/` | 上升词，`cursor`,`count` | `hotsearch`，应用级 token | [上升词](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/hot-video-data/get-ascending-words/) |
| GET `/hotsearch/videos/` | 热点词聚合的视频 | `hotsearch`，应用级 token | [热点视频](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/hot-video-data/get-hot-words-polymerization-video/) |

### 数据分析

以下接口为统计读取，不执行点赞、评论或分享。大多需要相关数据 scope、用户 OAuth 授权，数据常有次日更新与时间窗口限制。

| 方法、路径 | 数据 | 第一方来源 |
| --- | --- | --- |
| GET `/data/external/item/base/` | 单视频基础播放、赞、评、分享与平均观看时长 | [基础数据](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/video-data/get-basic-data/) |
| GET `/data/external/item/play/` | 单视频播放趋势 | [播放数据](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/video-data/get-play-data/) |
| GET `/data/external/item/like/` | 单视频点赞趋势 | [点赞数据](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/video-data/get-like-data/) |
| GET `/data/external/item/comment/` | 单视频评论趋势 | [评论数据](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/video-data/get-comment-data/) |
| GET `/data/external/item/share/` | 单视频分享趋势 | [分享数据](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/video-data/get-share-data/) |
| GET `/data/external/user/item/` | 用户作品总量趋势 | [用户视频情况](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/user-data/get-user-video-status/) |
| GET `/data/external/user/like/` | 用户获赞趋势 | [用户点赞数](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/user-data/get-user-like-number) |
| GET `/data/external/user/comment/` | 用户获评论趋势 | [用户评论数](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/user-data/get-user-comment-count/) |
| GET `/data/external/user/share/` | 用户获分享趋势 | [用户分享数](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/user-data/get-user-share-count/) |
| GET `/data/external/user/profile/` | 用户主页访问数 | [主页访问](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/user-data/get-user-home-pv) |
| GET `/data/external/user/fans/` | 用户粉丝趋势 | [用户粉丝数](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/user-data/get-user-fans-count/) |
| GET `/fans/data/` | 粉丝年龄、性别、地域画像 | [粉丝画像](https://open.douyin.com/platform/resource/docs/openapi/data-open-service/fans-portrait-data/get-user-fans-data/) |

### 企业私信与直播

| 方法、路径 / 形态 | 用途 | 第一方来源 |
| --- | --- | --- |
| POST `/enterprise/media/upload/` | 上传企业私信图片、PDF 等素材，返回 `media_id` | [素材上传](https://open.douyin.com/platform/resource/docs/openapi/tools-ability/material-management/upload-material-interface) |
| POST `/enterprise/im/message/send/` | 企业号发送文本、图片、已审核视频或卡片私信；非群聊 | [发送私信](https://open.douyin.com/platform/resource/docs/openapi/enterprise-open-ability/message-management-enterprise/message-to-user/) |
| Webhook 事件 | 企业号接收私信与会话动作 | [企业私信方案](https://open.douyin.com/platform/resource/docs/ability/enterprise-account-open-ability/message-solution/) |
| 直播 SDK | 看播、互动等通过受限 SDK 接入；该材料不提供可直接复用的网页 HTTP API | [直播 SDK 功能](https://open.douyin.com/platform/resource/docs/ability/douyin-live-sdk/introduction) |

**验证状态**：以上开放平台章节只核对了官方文档的路径、方法、scope 与描述；没有用 Cookie 执行任何开放平台请求，也没有执行投稿、评论、私信、关注、点赞、收藏或直播互动。网页 `www.douyin.com` 的实际抓包结果应独立列出，不可把这两种接口混在同一验证等级。
