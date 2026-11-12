# BiliSoul · B站全站接口目录

整理日期：2026-11-12（北京时间）

## 覆盖与证据

- 登录态浏览器抓包：原始 44 组、扩展 113 组，合并去重 126 组方法 + 主机 + 路径。扩展页面包含搜索、动态、个人空间、历史、收藏、稍后再看、私信入口、创作中心、直播间和漫画入口。
- B站开放平台：只读索引了 183 篇官方文档，提取 104 条生产环境 API 路径。文档还包含业务说明、回调和授权流程；这些行不一定有独立请求 URL。
- 用户交互写接口：由 B站当前网页加载的第一方 JavaScript 定位方法、路径和字段。评论发评以及本次视频笔记的图片上传、私人保存、公开提交已在用户指定内容上实际调用并回读；其余点赞、投币、动态、视频投稿、删除、私信和账号修改仍仅有脚本或文档证据。
- 凡浏览器自动发出的风控或播放统计 POST，只是页面副作用，不表示用户交互写入已经验证。打开页面可能自动更新阅读游标，详情见原始抓包文档。

**证据等级：** A = 登录态浏览器网络实测； W = 用户授权的实际写入并回读； S = 第一方网页脚本静态确认，未实发； O = 官方开放平台文档，未以应用凭据实调； ? = 路径或字段仍未确认。HTTP 200 不代表业务成功，仍需检查响应 code 和实际资源状态。

## 两种授权体系

| 系统 | 可覆盖场景 | 凭据与关键要求 |
| --- | --- | --- |
| 主站网页内部接口 | 评论、点赞、收藏、关注、动态、私信、账号资料等 | B站登录 Cookie；多数 POST 由网页注入 bili_jct 对应的 csrf，部分请求另需 WBI/风控处理。脚本证据不等于调用权限或稳定契约。 |
| 开放平台 API | 服务端视频投稿、专栏、直播、数据、电商等官方开放能力 | 应用入驻、相应 scope、用户 OAuth 授权、签名 v2 请求头；用户 Cookie 不能代替。各业务还有独立准入条件。 |

官方入口：[开放平台文档](https://open.bilibili.com/doc/) · [签名和状态码](https://open.bilibili.com/doc/4/8673959e-f7bb-56e6-6e68-d225f971b81b) · [文档未列出的功能](https://open.bilibili.com/doc/4/c381daac-4b6d-9ed3-3604-19a78d358eec)。官方明确存在未公开到文档的能力，因此本文是**已确认接口的目录**，不能称为 B站所有内部接口的穷尽清单。

## 一、视频投稿、查询、编辑和删除（O / S）

### 官方开放平台（O）

官方投稿需要 ARC_BASE 及用户授权。小文件走单文件上传，大文件走分片上传和合片；上传字节的 openupos 地址使用预处理返回的 upload_token。最终提交进入审核，并非立即公开。

| 操作 | 方法与生产路径 | 关键参数或请求体字段 | 官方文档 |
| --- | --- | --- | --- |
| 初始化上传 | POST member.bilibili.com/arcopen/fn/archive/video/init | JSON: name, utype（0 分片；1 为不超过 100MB 的单文件） | [预处理](https://open.bilibili.com/doc/4/0c532c6a-e6fb-0aff-8021-905ae2409095) |
| 分片上传 | POST openupos.bilivideo.com/video/v2/part/upload | query: upload_token, part_number；body 为裸二进制 | [分片](https://open.bilibili.com/doc/4/733a520a-c50f-7bb4-17cb-35338ba20500) |
| 合片 | POST member.bilibili.com/arcopen/fn/archive/video/complete | query: upload_token | [合片](https://open.bilibili.com/doc/4/0828e499-38d8-9e58-2a70-a7eaebf9dd64) |
| 单文件上传 | POST openupos.bilivideo.com/video/v2/upload | query: upload_token；body 为裸二进制 | [单文件](https://open.bilibili.com/doc/4/f22a0eee-c92d-0f1d-f69c-be170cf533c7) |
| 上传封面 | POST member.bilibili.com/arcopen/fn/archive/cover/upload | multipart: file；返回 data.url | [封面](https://open.bilibili.com/doc/4/8243399e-50e3-4058-7f01-1ebe4c632cf8) |
| 查询分区 | GET member.bilibili.com/arcopen/fn/archive/type/list | 响应中的二级分区 ID 用作 tid | [分区](https://open.bilibili.com/doc/4/4f13299b-5316-142f-df6a-87313eaf85a9) |
| 提交稿件 | POST member.bilibili.com/arcopen/fn/archive/add-by-utoken | query: upload_token；JSON 必填 title,tid,tag,copyright；可选 cover,no_reprint,desc,source,topic_id,mission_id | [投稿](https://open.bilibili.com/doc/4/f7fc57dd-55a1-5cb1-cba4-61fb2994bf0f) |
| 查询投稿列表 | GET member.bilibili.com/arcopen/fn/archive/viewlist | pn,ps,status；查看审核状态和驳回原因 | [列表](https://open.bilibili.com/doc/4/a24030b7-6b8f-b36c-32d8-a4aae67fcc35) |
| 查询单个稿件 | GET member.bilibili.com/arcopen/fn/archive/view | resource_id | [详情](https://open.bilibili.com/doc/4/d9554788-dcef-f139-6217-b487d41c3826) |
| 编辑元数据 | POST member.bilibili.com/arcopen/fn/archive/edit | JSON 必填 resource_id,title,tid；另可修改 cover,no_reprint,desc；重新审核 | [编辑](https://open.bilibili.com/doc/4/ddfbe54d-b4ab-340e-c698-933b9a3c619c) |
| 删除稿件 | POST member.bilibili.com/arcopen/fn/archive/delete | JSON: resource_id；删除不可逆 | [删除](https://open.bilibili.com/doc/4/23d78390-4119-1e5f-2bbe-b45bd5cecdb0) |

### 网页创作中心（S，使用登录 Cookie）

创作中心的[路由脚本](https://s1.hdslb.com/bfs/static/studio/creativecenter-platform-next/static/js/async/js/creativecenter-v3.2591.090082a0.js)把投稿页指向 member.bilibili.com/york/videoup?new。以下路径来自[网页投稿逻辑](https://s1.hdslb.com/bfs/static/creator-monorepo/videoup/static/js/index.74d99626.js)与[UPOS 上传库](https://s1.hdslb.com/bfs/static/creator-monorepo/videoup/static/js/100.72bee00e.js)，只做静态检查，没有用 Cookie 上传、存草稿或投稿。具体主机、鉴权头、必填条件应以运行时返回值和当前页面为准。

| 操作 | 方法与路径 | 已确认字段 / 顺序 |
| --- | --- | --- |
| 预上传 | GET member.bilibili.com/preupload | name,size,r,profile,ssl,version,build,webVersion,gaia_vtoken；返回 auth,upos_uri,biz_id,endpoint/endpoints |
| 创建 UPOS 上传 | POST 动态 UPOS URL?uploads&output=json | 头 X-Upos-Auth；返回 upload_id |
| 分片上传 | PUT 动态 UPOS URL | query: partNumber,uploadId,chunk,chunks,size,start,end,total,output；二进制 body 和 X-Upos-Auth |
| UPOS 合片 | POST 动态 UPOS URL | query: output,name,profile,uploadId,biz_id；JSON parts[] 内含 partNumber,eTag |
| 网页封面上传 | POST member.bilibili.com/x/vu/web/cover/up | FormData cover,csrf |
| 网页稿件提交 | POST member.bilibili.com/x/vu/web/add/v3 | query: web_location,t；body 常用 title,copyright,source,tid,tag,desc,desc_format_id,dtime,dynamic,videos[],cover,cover43,ai_cover,is_ab_cover,ab_cover_info,mission_id,topic_id,topic_detail,recreate,interactive；videos[] 常用 filename,title,desc,cid。条件字段需按实际投稿类型核对 |
| 网页稿件编辑 | POST member.bilibili.com/x/vu/web/edit | 同类稿件 body，另有 aid,new_web_edit |
| 草稿新增/更新 | POST member.bilibili.com/x/vupre/web/draft/add 或 /update | 稿件字段与草稿标识的组合仍待核对 |
| 草稿查看/列表 | GET member.bilibili.com/x/vupre/web/draft/view 或 /list | 网页静态脚本确认 |
| 草稿删除 | POST member.bilibili.com/x/vupre/web/draft/delete | 网页静态脚本确认；正文与成功判据待核对 |
| 投稿前视频校验 | POST member.bilibili.com/x/vupre/web/archive/videocheck | 网页静态脚本确认；正文待核对 |

UPOS 的真实主机和路径由预上传回包决定，不能把表中的“动态 UPOS URL”写成固定域名。投稿脚本中的一个 Axios 实例对其 POST 加 withCredentials 和 csrf（query/body），可确认封面、草稿、编辑、视频检查等请求的注入方式；稿件提交使用另一个 SDK，其 csrf 注入尚未直接确认。官方开放平台与网页创作中心是两套流程：前者需要应用 OAuth 和签名，后者使用网页登录态。网页提交 body 中存在 dynamic 字段，但当前没有确认其值如何影响视频动态，也未确认投稿后会自动发动态。官方开放平台目录未列视频草稿箱 API，网页创作中心则有单独草稿接口。

## 二、网页端评论、视频互动和关系（S）

下表来自[视频页脚本](https://s1.hdslb.com/bfs/static/jinkela/video/video.1db771781ee838fb7043ed37d224be7afd1ad4b8.js)与[评论组件脚本](https://s1.hdslb.com/bfs/seed/jinkela/commentpc/bili-comments.js)。评论 /x/v2/reply/add 已经在用户指定的开放评论视频上发评 code=0 并通过 GET 回读，另一条关闭评论的视频返回 code=12002；其余表项仍只经过脚本静态核对。视频评论的 oid 通常取视频 aid，type=1。

| 操作 | 方法与路径（api.bilibili.com） | 已确认字段名 / 动作 |
| --- | --- | --- |
| 发一级评论、回复 | POST /x/v2/reply/add | plat,oid,type,message；回复加 root,parent；可选 at_name_to_mid,pictures,sync_to_dynamic,has_vote_option,gaia_source |
| 评论图片上传 | POST /x/dynamic/feed/draw/upload_bfs | multipart: file_up,biz=new_dyn,category=daily；响应 image_url,image_width,image_height,img_size |
| 评论点赞或撤销 | POST /x/v2/reply/action | oid,type,rpid,action=1/0 |
| 评论点踩或撤销 | POST /x/v2/reply/hate | oid,type,rpid,action=1/0 |
| 删除评论 | POST /x/v2/reply/del | oid,type,rpid |
| 评论置顶或取消 | POST /x/v2/reply/top | oid,type,rpid,action=1/0 |
| 评论区设置 | POST /x/v2/reply/subject/modify | oid,type,action；action 枚举须针对当前页面再确认 |
| 举报评论 | POST /x/v2/reply/report | type,oid,rpid,reason,content,add_blacklist,delete,ordering,statistics |
| 评论投票 | POST /x/v2/reply/vote/do | option,vote_id,oid,type |
| 视频点赞或取消 | POST /x/web-interface/archive/like | aid,like=1/2 |
| 视频投币 | POST /x/web-interface/coin/add | aid,multiply,select_like,cross_domain |
| 视频一键三连 | POST /x/web-interface/archive/like/triple | aid |
| 收藏或移出收藏夹 | POST /x/v3/fav/resource/deal | rid,type=2,add_media_ids,del_media_ids,platform=web |
| 新建收藏夹 | POST /x/v3/fav/folder/add | title,privacy=0；其他隐私值需再确认 |
| 从收藏夹批量移出资源 | POST /x/v3/fav/resource/batch-del | platform,media_id,resources,from_spmid,spmid,statistics；[稍后再看/列表脚本](https://s1.hdslb.com/bfs/static/jinkela/playlist/playlist.3964f9530ace6a294ff0ebc2a9344bd416b55996.js) |
| 订阅或取消订阅别人的收藏夹 | POST /x/v3/fav/folder/fav 或 /unfav | platform,mobi_app,media_id,from_spmid,spmid,statistics；与管理自己的收藏夹不同 |
| 关注或取消关注 | POST /x/relation/modify | fid,act,re_src,spmid,extend_content,cross_domain,gaia_source；视频页关注 act=1，普通取关 act=2 |
| 稍后再看添加或删除 | POST /x/v2/history/toview/add 或 /del | aid,csrf |
| 视频分享计数 | POST /x/web-interface/share/add | aid；属于计数写入，不等于完成外部分享 |
| 合集收藏或取消 | POST /x/v3/fav/season/fav 或 /unfav | platform=web,season_id |
| 发普通弹幕 | POST /x/v2/dm/post | [播放器第一方脚本](https://s1.hdslb.com/bfs/static/player/main/core.a3c25289.js)只确认路径和方法；普通模式完整字段待确认 |
| 弹幕点赞、删除等 | POST /x/v2/dm/thumbup/add、/x/v2/dm/up/delete 等 | 播放器脚本只确认路径；具体权限、字段、成功条件待验证 |

自己的收藏夹编辑和删除未取得足够一手证据，暂不把网上流传的路径当作已确认接口。

## 三、动态：文字、图片、转发、点赞、删除（S，部分读取为 A）

证据：[B站动态页当前第一方脚本](https://s1.hdslb.com/bfs/static/2233-monorepo/dyn-home/static/js/index.ae117a6a.js)。图片须先上传拿到 image_url、宽高等，再组装 pics[]；发布前页面先调用提交检查。没有真正发动态或上传图片。

| 操作 | 方法与路径 | 已确认字段名 / 结果 |
| --- | --- | --- |
| 发布前权限检查 | GET api.bilibili.com/x/dynamic/feed/create/init_check | scene；扩展登录态抓包 code=0 |
| 动态图片上传 | POST api.bilibili.com/x/dynamic/feed/draw/upload_bfs | multipart: file_up,biz=dyn,category=daily；响应 image_url,image_width,image_height,ai_gen_pic |
| 提交前检查 | POST api.bilibili.com/x/dynamic/feed/create/submit_check | content,pics,attach_card,scene,create_option；编辑另有 dyn_id_str |
| 发布文字/图片动态 | POST api.bilibili.com/x/dynamic/feed/create/dyn?platform=web | body: dyn_req；纯文本 contents[] 项含 raw_text,type=1,biz_id；图片 pics[] 项含 img_src,img_width,img_height,img_size,ai_gen_pic，option.pic_mode |
| 编辑动态 | POST api.bilibili.com/x/dynamic/feed/edit/dyn | dyn_req 及原 dyn_id_str；字段组合需跟页面版本核对 |
| 转发动态 | POST api.bilibili.com/x/dynamic/feed/create/dyn?platform=web | scene=4 + web_repost_src.dyn_id_str；另一场景 scene=5 + web_repost_src.revs_id |
| 动态点赞或取消 | POST api.bilibili.com/x/dynamic/feed/dyn/thumb | dyn_id_str,up=1/2 |
| 删除动态 | POST api.bilibili.com/x/dynamic/feed/operate/remove?platform=web | dyn_id_str |
| 转发评论 | POST api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/reply | uid,type,rid,content,repost_code,from,at_uids,extension |
| 动态列表 | GET api.bilibili.com/x/polymer/web-dynamic/v1/feed/all | 已登录态浏览器抓到；具体分页见附录 |
| 旧版草稿添加、修改 | POST api.vc.bilibili.com/dynamic_draft/v1/dynamic_draft/add_draft 或 /modify_draft | type（有图 2 / 无图 4）,publish_time,request；修改加 draft_id |
| 旧版草稿列表、删除、立即发布 | GET /dynamic_draft/v1/dynamic_draft/get_drafts；POST /rm_draft 或 /publish_now | api.vc.bilibili.com；删除/立即发布带 draft_id |
| 新版定时动态列表和计数 | GET api.bilibili.com/x/polymer/web-dynamic/v1/timing/draft/list；GET /x/dynamic/feed/timing_dyn/count | 计数已浏览器实测；列表为静态脚本证据 |
| 新版定时动态删除或立即发布 | POST api.bilibili.com/x/dynamic/feed/timing_dyn/delete 或 /publish | dyn_id_str；发布还带 dyn_req |
| 直接排程新动态 | POST api.bilibili.com/x/dynamic/feed/create/dyn?platform=web | dyn_req.option.timer_pub_time 为秒级时间戳 |

普通动态评论使用上节评论体系，oid/type 取该动态响应的 basic.comment_id_str 与 basic.comment_type，不能固定成视频评论的 type=1。视频投稿走独立流程；当前未确认把新投稿自动关联成视频动态的请求体。官方开放平台目录未提供通用动态发布类目；以上均为主站网页内部接口。

## 四、视频笔记与思维导图图片（A / S / W）

依据[视频页第一方笔记脚本](https://s1.hdslb.com/bfs/seed/jinkela/material/bilinote.umd.min.js)核对；2026-11-12 已在用户授权的视频上实际上传图片、保存私人笔记、回读并提交公开审核。此次写入均返回业务 code=0；后续 pub_status=2，公开接口匿名读取 code=0。具体视频和笔记标识已省略。笔记使用视频 aid 作 oid，oid_type=0；B站当前限制每个视频一篇个人笔记。完整的笔记字段与状态见[独立接口记录](./video-note-api.md)。

| 操作 | 方法与路径（api.bilibili.com） | 字段与验证结果 |
| --- | --- | --- |
| 笔记入口状态 | GET /x/note/is_forbid | aid；本次返回 data.forbid_note_entrance=false |
| 当前用户的视频笔记列表 | GET /x/note/list/archive | oid,oid_type,csrf；data.noteIds |
| 读取私人笔记 | GET /x/note/info | oid,oid_type,note_id,csrf；data.title,content,summary,pub_status,pub_reason 等。本次私人保存后回读确认正文和图片 |
| 上传笔记图片 | POST /x/note/image/upload | multipart: file,csrf；返回 data.location；本次 code=0。返回 URL 可为 /x/note/image 路径，嵌入时使用返回值，不自行编造 /bfs/note 地址 |
| 保存私人笔记 | POST /x/note/add | form: from=save,oid,oid_type,note_id（新建为空）,title,summary,content,tags,cls=1,csrf,cont_len,hash,platform=web；返回 data.note_id；本次 code=0 |
| 提交公开发布 | POST /x/note/add | 在保存字段基础上加入 publish=1,original=1,auto_comment=0,comment_format=2 和已保存 note_id；本次 code=0，先回读 pub_status=1，后转 2；请求明确关闭自动评论 |
| 公开笔记列表 | GET /x/note/publish/list/archive | oid,oid_type,pn,ps,uper_mid（视频 UP 主 mid）；data.list[] 含 cvid,web_url,author.mid；审核通过后从这里取得公开链接 |
| 读取公开笔记 | GET /x/note/publish/info | cvid；授权实测回读 content,pub_status=2；匿名请求 code=0 |

content 是 Quill Delta op 数组的 JSON 字符串。纯文本 op 用 insert 字符串；图片 op 的 insert.imageUpload 含 id,source,status,url,width。cont_len 是编辑器长度，图片计 1；summary 来自去图片的文本摘要，tags 可放时间标签，未加可传空字符串。本次笔记把时间锚点作为普通文本，并嵌入上传后的思维导图 PNG。脚本中的 pub_status：0 未公开，1/5 审核中，2 审核通过，3/4/6 未通过；具体原因看 pub_reason。**公开提交成功不等于已通过审核。**

## 五、私信和账号（S，部分读取为 A）

第一方证据：[私信页脚本](https://s1.hdslb.com/bfs/static/2233-monorepo/message-pc/static/js/index.f9c057f6.js)、[账号页脚本](https://s1.hdslb.com/bfs/static/2233-monorepo/account/static/js/index.fdd38298.js)、[资料编辑脚本](https://s1.hdslb.com/bfs/static/2233-monorepo/account/static/js/async/390.4e62523b.js)、[头像脚本](https://s1.hdslb.com/bfs/static/2233-monorepo/account/static/js/async/711.7449c6ca.js)。没有发送私信或修改资料。

| 操作 | 方法与路径 | 已确认字段名 / 注意点 |
| --- | --- | --- |
| 会话列表 | GET api.vc.bilibili.com/session_svr/v1/session_svr/get_sessions | session_type,group_fold,unfollow_fold,sort_rule,begin_ts,end_ts,size,build,mobi_app |
| 新会话 | GET api.vc.bilibili.com/session_svr/v1/session_svr/new_sessions | 私信页面脚本静态确认 |
| 会话消息 | GET api.vc.bilibili.com/svr_sync/v1/svr_sync/fetch_session_msgs | size,session_type,talker_id,begin_seqno,end_seqno,sender_device_id,build,mobi_app |
| 发送普通私信 | POST api.vc.bilibili.com/web_im/v1/web_im/send_msg | msg[sender_uid],msg[receiver_type],msg[receiver_id],msg[msg_type],msg[msg_status],msg[content],msg[new_face_version],msg[canal_token],msg[dev_id],msg[timestamp]；另 from_firework,build,mobi_app；query 含 w_sender_uid,w_receiver_id,w_dev_id |
| 撤回普通私信 | POST 同一 send_msg | msg_type=5，content 为原消息 key；页面显示 2 分钟时限 |
| 获取账号资料 | GET api.bilibili.com/x/member/web/account | 账号页脚本静态确认 |
| 修改资料 | POST api.bilibili.com/x/member/web/update | uname,usersign,sex,birthday,source=profile_web；可选 handle |
| 更新头像 | POST api.bilibili.com/x/member/web/face/update?csrf=… | multipart: dopost,DisplayRank,face |
| 修改隐私设置 | POST api.bilibili.com/x/space/user/setting/modify | 具体 body 字段尚未确认 |

客服会话另走 customerservice.bilibili.com 的接口，不能与普通私信混用；详见附录官方“经营号客服”文档。

## 六、专栏与直播的官方开放能力（O）

| 操作 | 方法与路径 | 关键字段或流程 | 官方文档 |
| --- | --- | --- | --- |
| 专栏图片上传 | POST member.bilibili.com/arcopen/fn/article/upload/image | file；可选 watermark；返回 data.url/size | [图片](https://open.bilibili.com/doc/4/0eaa4d3e-c4c0-f874-6f3c-e083aa939a1b) |
| 专栏提交 | POST member.bilibili.com/arcopen/fn/article/add | 必填 title,category,template_id,summary,content；可选 banner_url,original,image_urls,tags,list_id,up_closed_reply,top_video_bvid | [文章提交](https://open.bilibili.com/doc/4/b14b77b6-8889-8c8b-2e83-17c5a4c550fb) |
| 专栏编辑或删除 | POST member.bilibili.com/arcopen/fn/article/edit 或 /delete | 删除 body ids；编辑字段见官方对应页 | [文章删除](https://open.bilibili.com/doc/4/b63f8918-2add-0fbb-0718-d0537329ed1c) |
| 获取开播授权 URL | GET member.bilibili.com/liveopen/fn/live/thirdPartyLive/grantUrl | biz_code,open_id,live_area_id,third_live_uuid；用户需移动端确认 | [开播授权](https://open.bilibili.com/doc/4/5827c4a4-aab6-235e-624b-a47248d712e3) |
| 开始直播 | POST member.bilibili.com/liveopen/fn/live/thirdPartyLive/startLive | biz_code,open_id,live_token；须先收授权回调 | [开始直播](https://open.bilibili.com/doc/4/cafd6cf4-be34-d2c6-4d43-ca309b7ad346) |
| 结束直播 | POST member.bilibili.com/liveopen/fn/live/thirdPartyLive/endLive | biz_code,open_id,live_key,third_live_uuid | [结束直播](https://open.bilibili.com/doc/4/e84cd5ba-68fe-effe-1835-c2a2ff22a72a) |

直播长连、房间信息、流信息和消息发送文档均在下方完整索引。官方直播弹幕发送属于限定商务接入，不能把路径猜成公开通用能力：[直播发送弹幕说明](https://open.bilibili.com/doc/4/d1276f50-2401-9202-9b63-097f63343e04)。

## 七、全站其他业务覆盖

官方文档按能力覆盖账号授权、用户管理、视频稿件、专栏、数据开放、直播、活动、经营号客服、交易电商、充电、课堂、数据资源、版权曲库、消息推送和沙盒。以下是本次官方目录中的篇数；每篇名称、生产接口和原文链接见附录 B。

| 官方分类 | 文档篇数 |
| --- | ---: |
| 消息推送 | 48 |
| 交易电商 | 45 |
| 直播能力 | 16 |
| 专栏稿件管理 | 14 |
| 视频稿件管理 | 14 |
| 经营号客服 | 7 |
| 数据开放服务 | 5 |
| 开放能力 | 4 |
| 接入指引 | 4 |
| 站内版权授权曲库 | 4 |
| 课堂业务 | 4 |
| 运营指南 | 4 |
| 新手指引 | 3 |
| 用户管理 | 3 |
| 充电业务 | 2 |
| 数据资源接入 | 2 |
| 活动接入 | 2 |
| 沙盒环境 | 1 |
| 限定接入文档 | 1 |

本次网页实测页面与方法 + 路径数如下。一个接口可能在多个页面出现，因此各行不能相加当作去重总数。

| 网页场景 | 请求形状数 |
| --- | ---: |
| 创作中心 | 34 |
| 稍后再看 | 32 |
| 个人空间 | 30 |
| 视频页与评论 | 30 |
| 收藏夹 | 21 |
| 动态 | 19 |
| 首页 | 16 |
| 搜索 | 14 |
| 私信 | 13 |
| 观看历史 | 13 |
| 回复我的 | 12 |
| 直播间 | 12 |
| 系统通知 | 12 |
| 提到我的 | 10 |
| 收到的赞 | 10 |
| 漫画 | 1 |

网页端还抓到搜索、观看历史、收藏夹、稍后再看、个人空间、动态、创作中心和直播间的读取接口；附录 A 给出完整方法与路径。漫画入口仅出现 1 组请求，尚未确认漫画业务接口，因此不填造具体漫画端点。更大范围的番剧、课堂购买、直播礼物、拉黑等网页写入接口没有逐项实发或脚本确认，统一标为待查；开放平台相关业务则按附录 B 的官方文档列出。

## 八、落到 BiliSoul 时的验证清单

1. 读取接口已可用现有 Cookie/WBI 方案，但逐条检查 HTTP 状态、业务 code、游标和返回字段。
2. 网页写接口中只有评论和视频笔记经过本次授权实发；其他操作实现前须针对具体动作核对当前网页提交的请求体、csrf/WBI、风控与资源结果。不要通过自动试发来“验证”用户账号。
3. 开放平台投稿和直播须先有对应开发者应用、scope 与 OAuth 授权；BiliSoul 当前 B站 Cookie 和 LLM 中转密钥不能直接调用开放平台写接口。
4. 图片动态与图片评论先上传文件，再把服务端返回的图片元数据放进发布请求。不能用本地文件路径直接代替图片 URL。

## 附录 A：浏览器网络请求全量脱敏清单

来源为此前 44 组首页、视频、消息抓包和本轮 113 组扩展页面抓包。合并去重后只保留页面标签、方法、主机、路径、查询参数**名称**、HTTP 状态和业务码；不保留 Cookie、请求正文、图片、聊天内容、用户 ID 或签名值。原始抓包文件未纳入公开仓库。

| 页面 | 方法 | 主机与路径 | 查询参数名称 | HTTP / code | 来源 |
| --- | --- | --- | --- | --- | --- |
| 视频页与评论 | GET | api.bilibili.com/x/activity/subject/info | bvid, sid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/click-interface/click/now | — | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | POST | api.bilibili.com/x/click-interface/click/web/h5 | w_aid, w_ftime, w_part, w_rid, w_stime, w_type, web_location, wts | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | POST | api.bilibili.com/x/click-interface/web/heartbeat | w_aid, w_dt, w_last_play_progress_time, w_mid, w_played_time, w_real_played_time, w_realtime, w_rid, w_start_ts, w_video_duration, web_location, wts | 200 / 0 | 原始抓包+扩展抓包 |
| 动态 | GET | api.bilibili.com/x/dynamic/feed/create/init_check | scene, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 动态 | GET | api.bilibili.com/x/dynamic/feed/dyn/banner | platform, position, web_location | 200 / 0 | 扩展抓包 |
| 动态 | GET | api.bilibili.com/x/dynamic/feed/timing_dyn/count | web_location | 200 / 0 | 扩展抓包 |
| 动态 | GET | api.bilibili.com/x/emote/user/panel/web | business, web_location | 200 / 0 | 扩展抓包 |
| 搜索、首页 | GET | api.bilibili.com/x/frontend/finger/spi | — | 200 / 0 | 原始抓包+扩展抓包 |
| 个人空间、创作中心、动态、回复我的、搜索、直播间、私信、观看历史、首页 | POST | api.bilibili.com/x/internal/gaia-gateway/ExClimbCongLing | — | 200 / 0 | 原始抓包+扩展抓包 |
| 个人空间、创作中心、动态、回复我的、提到我的、搜索、收到的赞、收藏夹、私信、稍后再看、系统通知、观看历史、视频页与评论、首页 | POST | api.bilibili.com/x/internal/gaia-gateway/ExClimbWuzhi | — | 200 / 0 | 原始抓包+扩展抓包 |
| 个人空间、创作中心、动态、回复我的、搜索、直播间、私信、观看历史、首页 | GET | api.bilibili.com/x/internal/gaia-gateway/ExGetAxe | — | 200 / 0 | 原始抓包+扩展抓包 |
| 个人空间、创作中心、动态、回复我的、提到我的、搜索、收到的赞、收藏夹、直播间、私信、稍后再看、系统通知、观看历史、视频页与评论、首页 | GET | api.bilibili.com/x/kv-frontend/namespace/data | appKey, nscode, unlimit, versionId | 200 / -304/0 | 原始抓包+扩展抓包 |
| 创作中心 | GET | api.bilibili.com/x/mcn/state | mcn_mid, x-bili-device-req-json, x-bili-locale-json | 200 / 82083 | 扩展抓包 |
| 提到我的 | GET | api.bilibili.com/x/msgfeed/at | build, mobi_app, platform, statistics, web_location, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 收到的赞 | GET | api.bilibili.com/x/msgfeed/like | build, mobi_app, platform, statistics, web_location, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 回复我的 | GET | api.bilibili.com/x/msgfeed/reply | build, mobi_app, platform, statistics, web_location, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 创作中心 | GET | api.bilibili.com/x/msgfeed/unread | build, mobi_app | 200 / 0 | 扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/note/is_forbid | aid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/note/list/archive | csrf, oid, oid_type | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/note/publish/list/archive | csrf, oid, oid_type, pn, ps, uper_mid | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/player/online/total | aid, bvid, cid, ts | 200 / 0 | 原始抓包+扩展抓包 |
| 直播间 | GET | api.bilibili.com/x/player/playurl | bvid, cid, fnval, platform | 200 / 0 | 扩展抓包 |
| 稍后再看 | GET | api.bilibili.com/x/player/wbi/playurl | app_id, avid, bvid, cid, client_attr, dm_cover_img_str, dm_img_inter, dm_img_list, dm_img_str, fnval, fnver, fourk, from_client, isGaiaAvoided, is_main_page, need_fragment, qn, session, version_name, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/player/wbi/v2 | aid, cid, dm_cover_img_str, dm_img_inter, dm_img_list, dm_img_str, isGaiaAvoided, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 私信 | GET | api.bilibili.com/x/polymer/pc-electron/v1/user/cards | build, mobi_app, statistics, uids, web_location, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 动态 | GET | api.bilibili.com/x/polymer/web-dynamic/v1/feed/all | features, page, platform, timezone_offset, type, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 动态 | GET | api.bilibili.com/x/polymer/web-dynamic/v1/portal | up_list_more, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/polymer/web-space/home/seasons_series | mid, page_num, page_size, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 首页 | GET | api.bilibili.com/x/product/user/recommendation/follow-up/recent/whitelist/status | web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 私信 | GET | api.bilibili.com/x/relation/blacks | cross_domain, statistics, web_location, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 搜索 | GET | api.bilibili.com/x/relation/relations | fids, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间、收藏夹 | GET | api.bilibili.com/x/relation/stat | vmid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/bangumi/follow/list | type, vmid, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/coin/video | vmid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 收藏夹 | GET | api.bilibili.com/x/space/fav/nav | mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/lastplaygame/v2 | mid, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/like/video | vmid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/masterpiece | vmid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间、收藏夹 | GET | api.bilibili.com/x/space/navnum | mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/notice | mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/reservation | vmid, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间、收藏夹 | GET | api.bilibili.com/x/space/setting | mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/top/arc | vmid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 53016 | 扩展抓包 |
| 个人空间、收藏夹 | GET | api.bilibili.com/x/space/upstat | mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间、收藏夹 | GET | api.bilibili.com/x/space/v2/myinfo | web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间、收藏夹 | GET | api.bilibili.com/x/space/wbi/acc/info | dm_cover_img_str, dm_img_inter, dm_img_list, dm_img_str, mid, platform, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间、收藏夹 | GET | api.bilibili.com/x/space/wbi/acc/relation | mid, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / -403/0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/wbi/arc/search | dm_cover_img_str, dm_img_inter, dm_img_list, dm_img_str, index, mid, order, order_avoided, platform, pn, ps, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/space/wbi/article | mid, platform, pn, ps, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 视频页与评论 | GET | api.bilibili.com/x/sunflower/artifex/toy/video/toy | aid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 稍后再看 | GET | api.bilibili.com/x/v1/medialist/info | biz_id, tid, type, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/v2/dm/wbi/web/seg.so | oid, pe, pid, ps, pull_mode, segment_index, type, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / — | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/v2/dm/web/view | duration, oid, pid, type, w_rid, web_location, without_subtitle, wts, x-bili-device-req-json, x-bili-locale-json | 200 / — | 原始抓包+扩展抓包 |
| 观看历史 | GET | api.bilibili.com/x/v2/history/shadow | web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 稍后再看 | GET | api.bilibili.com/x/v2/medialist/toview/web | add_time_end, add_time_start, arc_max_duration, arc_min_duration, desc, direction, mobi_app, oid, otype, pn, preview, ps, use_pn, viewed, web_location, with_current, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 视频页与评论 | GET | api.bilibili.com/x/v2/reply/subject/description | oid, type, web_location, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 创作中心 | GET | api.bilibili.com/x/v2/reply/up/fulllist | order, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 视频页与评论 | GET | api.bilibili.com/x/v2/reply/wbi/main | extra, mode, oid, pagination_str, plat, type, w_rid, web_location, wts, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/v2/subtitle/web/view | context_ext, cur_production_type, oid, pid, playlist_switch, type, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / — | 原始抓包+扩展抓包 |
| 收藏夹 | GET | api.bilibili.com/x/v3/fav/folder/collected/list | platform, pn, ps, up_mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间 | GET | api.bilibili.com/x/v3/fav/folder/created/list | pn, ps, up_mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 收藏夹 | GET | api.bilibili.com/x/v3/fav/folder/created/list-all | up_mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 收藏夹 | GET | api.bilibili.com/x/v3/fav/folder/season/show | web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 收藏夹 | GET | api.bilibili.com/x/v3/fav/resource/list | media_id, order, platform, pn, ps, tid, type, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间、动态、回复我的、提到我的、搜索、收到的赞、收藏夹、私信、稍后再看、系统通知、观看历史、视频页与评论、首页 | GET | api.bilibili.com/x/vip/ads/materials | buvid, platform, position | 200 / 0 | 原始抓包+扩展抓包 |
| 创作中心 | GET | api.bilibili.com/x/web-frontend/risk/config | — | 200 / — | 扩展抓包 |
| 稍后再看 | GET | api.bilibili.com/x/web-interface/archive/related | bvid, from_spmid, need_operation_card, spmid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/web-interface/archive/relation | aid, bvid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/web-interface/broadcast/servers | platform | 200 / 0 | 原始抓包+扩展抓包 |
| 动态 | GET | api.bilibili.com/x/web-interface/dynamic/card/type | web_location | 200 / 0 | 扩展抓包 |
| 个人空间、回复我的、提到我的、搜索、收到的赞、收藏夹、私信、稍后再看、系统通知、观看历史、视频页与评论、首页 | GET | api.bilibili.com/x/web-interface/dynamic/entrance | alltype_offset, article_offset, video_offset, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 首页 | GET | api.bilibili.com/x/web-interface/history/continuation | his_exp, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 观看历史 | GET | api.bilibili.com/x/web-interface/history/cursor | max, ps, type, view_at, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 个人空间、创作中心、动态、回复我的、提到我的、搜索、收到的赞、收藏夹、漫画、私信、稍后再看、系统通知、观看历史、视频页与评论、首页 | GET | api.bilibili.com/x/web-interface/nav | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/web-interface/relation | mid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 搜索 | GET | api.bilibili.com/x/web-interface/suggest | highlight, spmid, term, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/web-interface/view/cards | aid, bvid, cid, platform, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/web-interface/view/conclusion/judge | bvid, cid, up_mid, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 稍后再看、视频页与评论 | GET | api.bilibili.com/x/web-interface/view/uplikeimg | aid, vmid, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 首页 | GET | api.bilibili.com/x/web-interface/wbi/index/top/feed/rcmd | brush, device, domestic_other_ps, domestic_zh_ps, feed_version, fetch_row, fresh_idx, fresh_idx_1h, fresh_type, homepage_ver, last_showlist, last_y_num, overseas_other_ps, overseas_zh_ps, ps, screen, uniq_id, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json, y_num | 200 / 0 | 原始抓包 |
| 个人空间、动态、回复我的、提到我的、搜索、收到的赞、收藏夹、私信、稍后再看、系统通知、观看历史、视频页与评论、首页 | GET | api.bilibili.com/x/web-interface/wbi/search/default | w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 动态 | GET | api.bilibili.com/x/web-interface/wbi/search/square | limit, platform, w_rid, web_location, wts | 200 / 0 | 扩展抓包 |
| 稍后再看 | GET | api.bilibili.com/x/web-interface/wbi/view/detail | aid, dm_cover_img_str, dm_img_inter, dm_img_list, dm_img_str, isGaiaAvoided, need_view, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心、动态、首页 | GET | api.bilibili.com/x/web-show/res/locs | ids, pf, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 个人空间、动态、回复我的、提到我的、搜索、收到的赞、收藏夹、私信、稍后再看、系统通知、观看历史、视频页与评论、首页 | GET | api.bilibili.com/x/web-show/wbi/res/locs | ids, pf, w_rid, web_location, wts, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 直播间 | GET | api.live.bilibili.com/live/getRoundPlayVideo | a, room_id, type | 200 / 0 | 扩展抓包 |
| 直播间 | GET | api.live.bilibili.com/xlive/app-ucenter/v1/resource/getResource | w_rid, web_location, wts | 200 / 0 | 扩展抓包 |
| 直播间 | GET | api.live.bilibili.com/xlive/general-interface/v1/content/get | key, t | 200 / 0 | 扩展抓包 |
| 直播间 | GET | api.live.bilibili.com/xlive/general-interface/v1/content/getRevenueMd5 | t | 200 / 0 | 扩展抓包 |
| 直播间 | GET | api.live.bilibili.com/xlive/mcn-interface/v1/homePage/CenterEntryIsShow | — | 200 / 0 | 扩展抓包 |
| 直播间 | GET | api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo | id, type, w_rid, web_location, wts | 200 / 0 | 扩展抓包 |
| 直播间 | GET | api.live.bilibili.com/xlive/web-room/v1/index/getIpInfo | — | 200 / 0 | 扩展抓包 |
| 稍后再看 | GET | api.live.bilibili.com/xlive/web-room/v1/index/getRoomBaseInfo | req_biz, uids, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 直播间 | GET | api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo | codec, dolby, eotf, format, panorama, platform, protocol, ptype, qn, req_reason, room_id, supported_drms, w_rid, web_location, wts | 200 / 0 | 扩展抓包 |
| 个人空间、动态、回复我的、提到我的、搜索、收到的赞、收藏夹、私信、稍后再看、系统通知、观看历史、视频页与评论、首页 | GET | api.vc.bilibili.com/x/im/web/msgfeed/unread | build, mobi_app, statistics, web_location, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 回复我的、提到我的、收到的赞、私信、系统通知 | GET | api.vc.bilibili.com/x/im/web/toast_msg | build, mobi_app, statistics, web_location, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |
| 动态 | GET | app.bilibili.com/x/topic/pub/rcmd/search | upload_id, web_location | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | cool.bilibili.com/x/co-create/material/list | material_type, ps, t | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | cool.bilibili.com/x/co-create/music/list | ps, t | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/vupre/web/archive/adorder/list | — | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/vupre/web/archive/white | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/activity/index | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/danmu/recent | pn, ps, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/data/archive/stat/query/latest | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/data/article | mid, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/data/fan | mid, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/data/index/stat | tmid, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/data/v2/grey | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/elec/balance | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/elec/income_center | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/elec/user | — | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/feedback/newtags | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/index/full | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/index/newcomer | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/index/scrolls | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/index/tool | type, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/openscreen/list | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/pagetip/list | page, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | member.bilibili.com/x/web/white | — | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | message.bilibili.com/api/notify/get.uplm.list.do | x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 扩展抓包 |
| 创作中心 | GET | message.bilibili.com/api/tooltip/query.list.do | — | 200 / 0 | 扩展抓包 |
| 系统通知 | GET | message.bilibili.com/x/sys-msg/query_unified_notify | build, mobi_app, page_size, statistics, web_location, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 系统通知 | GET | message.bilibili.com/x/sys-msg/query_user_notify | build, mobi_app, page_size, statistics, web_location, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 系统通知 | GET | message.bilibili.com/x/sys-msg/update_cursor | build, cursor, has_up, mobi_app, statistics, web_location, x-bili-locale-json | 200 / 0 | 原始抓包 |
| 个人空间、搜索、收藏夹、稍后再看、观看历史、视频页与评论、首页 | GET | passport.bilibili.com/x/passport-login/web/cookie/info | csrf, web_location, x-bili-device-req-json, x-bili-locale-json | 200 / 0 | 原始抓包+扩展抓包 |

## 附录 B：官方开放平台文档完整索引

本索引来自 B站开放平台自己的公开文档目录，列出本次能读取的全部 183 篇文章。接口栏只收生产环境中明确出现的 B站开放平台 URL；“说明/回调/无生产 URL”表示该篇没有可确认的独立生产请求路径，不代表没有业务价值。文档中示例的 mock、uat 和临时签名链接均已排除。若同一文章出现多个 URL，可能是正文中的相关接口引用，具体请求方法仍应点开对应原文核对。

| 官方分类 | 文档 | 文档标注方法 | 文内生产 API 路径 | 原文 |
| --- | --- | --- | --- | --- |
| 其他 / 限定接入文档 | 本路径文档说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/f15d8851-f741-d949-16e1-aeaff78e53ca) |
| 开放能力 | 接口权限白名单 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/b2dc2f0e-c874-aed7-3d92-360929e79d3a) |
| 开放能力 | 接口签名和状态码 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/8673959e-f7bb-56e6-6e68-d225f971b81b) |
| 开放能力 | 文档中未列出的功能 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/c381daac-4b6d-9ed3-3604-19a78d358eec) |
| 开放能力 | 账号授权 | — | https://api.bilibili.com/x/account-oauth2/v1/refresh_token<br>https://api.bilibili.com/x/account-oauth2/v1/token | [官方文档](https://open.bilibili.com/doc/4/eaf0e2b5-bde9-b9a0-9be1-019bb455701c) |
| 开放能力 / 专栏稿件管理 / 图片上传 | 专栏稿件图片上传 | POST | https://member.bilibili.com/arcopen/fn/article/upload/image | [官方文档](https://open.bilibili.com/doc/4/0eaa4d3e-c4c0-f874-6f3c-e083aa939a1b) |
| 开放能力 / 专栏稿件管理 / 文章管理 | 文章删除 | POST | https://member.bilibili.com/arcopen/fn/article/delete | [官方文档](https://open.bilibili.com/doc/4/b63f8918-2add-0fbb-0718-d0537329ed1c) |
| 开放能力 / 专栏稿件管理 / 文章管理 | 文章提交 | POST | https://member.bilibili.com/arcopen/fn/article/add | [官方文档](https://open.bilibili.com/doc/4/b14b77b6-8889-8c8b-2e83-17c5a4c550fb) |
| 开放能力 / 专栏稿件管理 / 文章管理 | 文章编辑 | POST | https://member.bilibili.com/arcopen/fn/article/edit | [官方文档](https://open.bilibili.com/doc/4/2b5284bd-9a40-247b-8da6-0ef7cd00afd3) |
| 开放能力 / 专栏稿件管理 / 文章管理 / 查看文章 | 查询文章列表 | GET | https://member.bilibili.com/arcopen/fn/article/list | [官方文档](https://open.bilibili.com/doc/4/c8057666-2b92-fc72-3607-f4199933dc13) |
| 开放能力 / 专栏稿件管理 / 文章管理 / 查看文章 | 查询文章详情 | GET | https://member.bilibili.com/arcopen/fn/article/detail | [官方文档](https://open.bilibili.com/doc/4/243457f6-9d44-9348-06ef-366cdbb44eb4) |
| 开放能力 / 专栏稿件管理 / 文章管理 / 查看文章 | 获取文章的分类列表 | GET | https://member.bilibili.com/arcopen/fn/article/categories | [官方文档](https://open.bilibili.com/doc/4/120b97a6-24a1-4e9f-47b7-9a201196e5d3) |
| 开放能力 / 专栏稿件管理 / 文章管理 / 查看文章 | 获取视频、文章卡片信息 | GET | https://member.bilibili.com/arcopen/fn/article/card<br>https://member.bilibili.com/arcopen/fn/article/cards | [官方文档](https://open.bilibili.com/doc/4/225be808-a81a-cd82-7703-1bbd601e243d) |
| 开放能力 / 专栏稿件管理 / 文集管理 | 文集删除 | POST | https://member.bilibili.com/arcopen/fn/article/anthology/delete | [官方文档](https://open.bilibili.com/doc/4/93289fec-1521-1f3f-c3ec-78108b4c7859) |
| 开放能力 / 专栏稿件管理 / 文集管理 | 文集提交 | POST | https://member.bilibili.com/arcopen/fn/article/anthology/add | [官方文档](https://open.bilibili.com/doc/4/728b35c7-21f9-d15e-6f0e-5e39c6647903) |
| 开放能力 / 专栏稿件管理 / 文集管理 / 文集编辑 | 文集下文章列表修改 | POST | https://member.bilibili.com/arcopen/fn/article/belong | [官方文档](https://open.bilibili.com/doc/4/b20487b7-471b-0717-b3b6-e65dd8a5263d) |
| 开放能力 / 专栏稿件管理 / 文集管理 / 文集编辑 | 文集信息编辑 | POST | https://member.bilibili.com/arcopen/fn/article/anthology/edit | [官方文档](https://open.bilibili.com/doc/4/0e2f82f8-8b16-2927-0546-ac1a24871501) |
| 开放能力 / 专栏稿件管理 / 文集管理 / 查看文集 | 查询文集列表 | GET | https://member.bilibili.com/arcopen/fn/article/anthology/list | [官方文档](https://open.bilibili.com/doc/4/1caef1c1-0576-91e3-00ed-c287e9866d7e) |
| 开放能力 / 专栏稿件管理 / 文集管理 / 查看文集 | 查询文集详情 | GET | https://member.bilibili.com/arcopen/fn/article/anthology/articles<br>https://member.bilibili.com/arcopen/fn/article/anthology/detail | [官方文档](https://open.bilibili.com/doc/4/78228e26-1c25-5b65-e107-a08dabf45850) |
| 开放能力 / 交易电商 / 带货 / 接口 | 商品推广链接生成 | POST | https://member.bilibili.com/arcopen/fn/market/live/commerce/generate/promotion/url | [官方文档](https://open.bilibili.com/doc/4/1a5d2f80-cfce-6c59-694f-caa52dc63e5e) |
| 开放能力 / 交易电商 / 用户票务信息 | 服务说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/349a99df-0ef5-21a8-7fc0-39b1440f0531) |
| 开放能力 / 交易电商 / 用户票务信息 / 接口 | 敏感信息解密 | POST | https://member.bilibili.com/arcopen/fn/common/market_ticket_decrypt | [官方文档](https://open.bilibili.com/doc/4/d1c6ef20-cdab-b72d-b5fe-daaff44a7096) |
| 开放能力 / 交易电商 / 用户票务信息 / 接口 | 用户优先购信息 | POST | https://member.bilibili.com/arcopen/fn/common/market_create_early_purchase | [官方文档](https://open.bilibili.com/doc/4/bfe2b347-1b31-eb14-f749-87391a3eab13) |
| 开放能力 / 交易电商 / 电商 | 服务说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/7b2f7f12-46ba-9de5-a6a3-6941dc3763d4) |
| 开放能力 / 交易电商 / 电商 / 接口 / 售后模块接口 | 售后详情 | POST | https://member.bilibili.com/arcopen/fn/market/common/after_sale_query_detail | [官方文档](https://open.bilibili.com/doc/4/2e7847b9-7bfc-2779-9935-1d7ca2bbefed) |
| 开放能力 / 交易电商 / 电商 / 接口 / 售后模块接口 | 售后列表查询 | POST | https://member.bilibili.com/arcopen/fn/market/common/after_sale_query_list | [官方文档](https://open.bilibili.com/doc/4/f47c96e6-6cd4-dd6c-1f22-7100e308f83f) |
| 开放能力 / 交易电商 / 电商 / 接口 / 售后模块接口 | 售后审核 | POST | https://member.bilibili.com/arcopen/fn/market/common/after_sale_check_after_sale | [官方文档](https://open.bilibili.com/doc/4/f1e88eaa-f55f-b9bc-7ca9-71048547f79e) |
| 开放能力 / 交易电商 / 电商 / 接口 / 售后模块接口 | 售后终止 | POST | https://member.bilibili.com/arcopen/fn/market/common/after_sale_stop | [官方文档](https://open.bilibili.com/doc/4/bf742d6f-fc65-e45d-de20-89634ec64b0f) |
| 开放能力 / 交易电商 / 电商 / 接口 / 售后模块接口 | 换货发货 | POST | https://member.bilibili.com/arcopen/fn/market/common/after_sale_barter_ship | [官方文档](https://open.bilibili.com/doc/4/4be43bcd-a2f0-3030-14ae-0c72a969b0b8) |
| 开放能力 / 交易电商 / 电商 / 接口 / 售后模块接口 | 确认收货 | POST | https://member.bilibili.com/arcopen/fn/market/common/after_sale_confirm_receipt | [官方文档](https://open.bilibili.com/doc/4/ae22993c-4494-b8b2-34fd-799e2883b89c) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 删除商品 | POST | https://member.bilibili.com/arcopen/fn/market/common/product_del | [官方文档](https://open.bilibili.com/doc/4/499a9223-2e6d-40c7-9dd0-4c91cafecd47) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 商品发布 | POST | https://member.bilibili.com/arcopen/fn/market/common/product_add | [官方文档](https://open.bilibili.com/doc/4/daf371c8-66b9-810d-1690-2ef366b441e7) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 图片上传 | POST | https://member.bilibili.com/arcopen/fn/v2/market/commodity/image/upload | [官方文档](https://open.bilibili.com/doc/4/cd8fe02e-6e28-dd41-3639-7f8a6a3f1da5) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 查询发品配置 | POST | https://member.bilibili.com/arcopen/fn/market/common/product_get_product_publish_rule | [官方文档](https://open.bilibili.com/doc/4/eeeb1517-9d0d-df0f-215f-d921c60ec810) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 查询商品列表 | GET | https://member.bilibili.com/arcopen/fn/v2/market/commodity/item/list | [官方文档](https://open.bilibili.com/doc/4/585ef2a5-00f7-eaad-ac41-244b4437b767) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 查询商品类目属性列表 | POST | https://member.bilibili.com/arcopen/fn/market/common/product_get_cate_property | [官方文档](https://open.bilibili.com/doc/4/03b7c473-f103-1abd-1f8a-ec874f273f03) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 查询商品详情 | POST | https://member.bilibili.com/arcopen/fn/market/common/product_detail | [官方文档](https://open.bilibili.com/doc/4/d930194e-423b-dc9f-a933-b35577342dda) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 查询类目列表 | GET | https://member.bilibili.com/arcopen/fn/market/commodity/category/qualified/list | [官方文档](https://open.bilibili.com/doc/4/940506ed-7e07-118d-ab37-a139a1195258) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 添加商品定制信息 | POST | https://member.bilibili.com/arcopen/fn/common/market_add_customization_product | [官方文档](https://open.bilibili.com/doc/4/3c071100-c661-8215-ab3e-5dd30d866f94) |
| 开放能力 / 交易电商 / 电商 / 接口 / 商品模块接口 | 编辑商品 | POST | https://member.bilibili.com/arcopen/fn/market/common/product_edit | [官方文档](https://open.bilibili.com/doc/4/9cecffa2-3850-ee10-e784-3457a8f34da5) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 发货回调 | POST | https://member.bilibili.com/arcopen/fn/market/common/logistics_add | [官方文档](https://open.bilibili.com/doc/4/50637383-99f9-f74f-954c-7fccb2d4f3fd) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 地址库创建 | POST | https://member.bilibili.com/arcopen/fn/market/common/address_create | [官方文档](https://open.bilibili.com/doc/4/3a73d5dd-ea6e-d326-1c0c-454830f5615e) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 批量查询地址库列表 | POST | https://member.bilibili.com/arcopen/fn/market/common/address_list | [官方文档](https://open.bilibili.com/doc/4/89223b4c-7231-21c2-f4d1-12de6fc75a5b) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 根据省获取全量三级地址 | POST | https://member.bilibili.com/arcopen/fn/market/common/address_get_areas_by_province | [官方文档](https://open.bilibili.com/doc/4/14937fb9-fbc6-9908-e326-89ce950dcd5e) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 游戏账号交易发货 | POST | https://member.bilibili.com/arcopen/fn/common/market_add_virtual_logistics | [官方文档](https://open.bilibili.com/doc/4/141be4c5-a0c3-b83e-1434-75721afc7da9) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 物流更新 | POST | https://member.bilibili.com/arcopen/fn/market/common/logistics_edit | [官方文档](https://open.bilibili.com/doc/4/09a62f63-dbe5-a60d-369c-dd76daeb531b) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 获取全量省份信息 | POST | https://member.bilibili.com/arcopen/fn/market/common/address_get_province | [官方文档](https://open.bilibili.com/doc/4/84f11a70-48ca-5ace-437a-496dd8be98c5) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 获取快递公司列表 | POST | https://member.bilibili.com/arcopen/fn/market/common/logistics_company_list | [官方文档](https://open.bilibili.com/doc/4/aa8e6518-d79b-3d47-38ca-ccb1c9b54d40) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 | 运费模板列表查询 | POST | https://member.bilibili.com/arcopen/fn/market/common/logistics_freight_template_list | [官方文档](https://open.bilibili.com/doc/4/11a253fe-04fd-157d-faf3-71ee27473ae4) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 / 文件上传 | 上传文件 | PUT | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/923578c8-3542-1e68-474b-226366cf7197) |
| 开放能力 / 交易电商 / 电商 / 接口 / 履约模块接口 / 文件上传 | 获取预授权上传地址 | POST | https://member.bilibili.com/arcopen/fn/common/market_get_upload_url | [官方文档](https://open.bilibili.com/doc/4/61631acd-3881-b86e-194e-24f3b523e7c5) |
| 开放能力 / 交易电商 / 电商 / 接口 / 库存模块接口 | 库存更新 | POST | https://member.bilibili.com/arcopen/fn/v2/market/stock/update | [官方文档](https://open.bilibili.com/doc/4/8261c899-6aaa-cde8-1536-a134e5ed0eac) |
| 开放能力 / 交易电商 / 电商 / 接口 / 库存模块接口 | 查询库存 | GET | https://member.bilibili.com/arcopen/fn/v2/market/stock/query | [官方文档](https://open.bilibili.com/doc/4/50dbb5e0-301c-90ce-ba2f-61446cf83a9c) |
| 开放能力 / 交易电商 / 电商 / 接口 / 店铺模块接口 | 获取店铺信息 | GET | https://member.bilibili.com/arcopen/fn/v2/market/shop/info/get | [官方文档](https://open.bilibili.com/doc/4/2f96ad40-bf3e-9ffd-d350-88a67e2c0df6) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 主动关单 | POST | https://member.bilibili.com/arcopen/fn/market/common/close_order | [官方文档](https://open.bilibili.com/doc/4/e28d00f0-101a-3468-91cc-9cc921d93f74) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 修改订单地址 | POST | https://member.bilibili.com/arcopen/fn/market/common/address_apply_status<br>https://member.bilibili.com/arcopen/fn/market/common/address_modify | [官方文档](https://open.bilibili.com/doc/4/0e70dfe2-7345-1f92-b357-c67328f9f92f) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 商家回传订单审核结果 | POST | https://member.bilibili.com/arcopen/fn/market/common/order_review | [官方文档](https://open.bilibili.com/doc/4/21d01097-ee1a-d0e7-6048-ed857ad0830a) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 商家备注 | POST | https://member.bilibili.com/arcopen/fn/market/common/order_remark | [官方文档](https://open.bilibili.com/doc/4/d57519e4-240e-be2b-4949-cdddb0c56c2c) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 带货订单查询 | POST | https://member.bilibili.com/arcopen/fn/market/common/page | [官方文档](https://open.bilibili.com/doc/4/a4d1450d-9239-5dce-6508-95edc2a0f334) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 抽卡机抽卡结果回调 | — | https://member.bilibili.com/arcopen/fn/market/common/callback | [官方文档](https://open.bilibili.com/doc/4/ed0d3f32-fa07-e185-0d62-752d6686d368) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 收单 | POST | https://member.bilibili.com/arcopen/fn/market/common/accept_order | [官方文档](https://open.bilibili.com/doc/4/0c64b075-4968-e1f6-4485-8ff0bc8964b0) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 订单列表查询 | POST | https://member.bilibili.com/arcopen/fn/market/common/order_searchList<br>https://member.bilibili.com/arcopen/fn/market/common/order_searchlist | [官方文档](https://open.bilibili.com/doc/4/bc224c89-48af-0635-6afd-72b3169015e3) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 订单敏感信息解密 | POST | https://member.bilibili.com/arcopen/fn/market/common/order_batch_decrypt | [官方文档](https://open.bilibili.com/doc/4/26ca9d40-db17-af60-c127-463d044675a8) |
| 开放能力 / 交易电商 / 电商 / 接口 / 订单模块接口 | 订单详情 | POST | https://member.bilibili.com/arcopen/fn/market/common/order_detail | [官方文档](https://open.bilibili.com/doc/4/7ce41b9f-9b9b-7a00-6fff-3e7df55b5bab) |
| 开放能力 / 充电业务 | 服务说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/a241f8ef-9ef5-5002-6aab-6de818e6f82b) |
| 开放能力 / 充电业务 / 接口 | 查询充电记录 | POST | https://member.bilibili.com/arcopen/fn/common/charge_order_search_list | [官方文档](https://open.bilibili.com/doc/4/21c29723-ad86-a1a5-44d3-5e8d7c6a58a4) |
| 开放能力 / 数据开放服务 / 专栏数据 | 获取单一专栏数据 | GET | https://member.bilibili.com/arcopen/fn/data/art/stat | [官方文档](https://open.bilibili.com/doc/4/46903ddc-1264-ddac-a3c7-559d12f32118) |
| 开放能力 / 数据开放服务 / 专栏数据 | 获取整体专栏增量数据 | GET | https://member.bilibili.com/arcopen/fn/data/art/inc-stats | [官方文档](https://open.bilibili.com/doc/4/f5d81e34-ab1b-ac92-2c5e-34c3c0d33828) |
| 开放能力 / 数据开放服务 / 用户数据 | 获取用户数据 | GET | https://member.bilibili.com/arcopen/fn/data/user/stat | [官方文档](https://open.bilibili.com/doc/4/90936ab5-7c06-e24f-2ad0-0fd6e10c7386) |
| 开放能力 / 数据开放服务 / 视频数据 | 获取单视频数据 | GET | https://member.bilibili.com/arcopen/fn/data/arc/stat | [官方文档](https://open.bilibili.com/doc/4/3f46ac2e-1318-3aa0-5548-0d9fd624d520) |
| 开放能力 / 数据开放服务 / 视频数据 | 获取整体视频增量数据 | GET | https://member.bilibili.com/arcopen/fn/data/arc/inc-stats | [官方文档](https://open.bilibili.com/doc/4/708a4ce5-5a6e-d8ce-b2e8-ff8a26a83b05) |
| 开放能力 / 数据资源接入 | 三方通用资源接口 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/7dddb3b5-afe9-7207-2316-9717a133b60e) |
| 开放能力 / 数据资源接入 | 接入指引 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/7e8744b0-f52d-9f9c-d946-de0dbd52e2ae) |
| 开放能力 / 沙盒环境 | 沙盒 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/c5fcba1e-58eb-2f84-c86b-88028b0656c0) |
| 开放能力 / 活动接入 | 接入指引 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/8042b95d-766c-48a1-60e2-3b9f8942503d) |
| 开放能力 / 活动接入 | 通用奖励接口 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/faf7daa6-3edc-17a3-3b09-74d0fbdcfc78) |
| 开放能力 / 消息推送 | 概述 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/b369a652-0e26-8ddb-74f0-20c74234fcd6) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 买家发起售后申请消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/f28b670e-1104-22d0-81d7-bb0a618d067f) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 买家发起客服仲裁消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/9aa0f013-f32c-ac4f-4bd5-8e1359a2b890) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 买家取消仲裁消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/7070a20d-a7ad-7895-afcf-df7dcbdbf219) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 买家退货消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/371337c3-051b-c40a-b64b-08aad3668ac6) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 仲裁客服介入消息消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/cf4028f7-d82b-dac8-55ae-c8927cc5a1d8) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 协商期商家上传凭证消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/53f4ae1b-6560-f273-e066-c359c9010884) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 同意售后申请消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/998ef957-d100-0e2b-6116-748c7cc05eee) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 售后取消消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/b2bd0d8d-7742-bf7c-ab3b-40b630aec235) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 客服仲裁结果消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/bfb344ac-64bf-54ba-89a9-72f3ecee3116) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 拒绝退款消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/16c0bd19-cbe4-f806-47e5-2f88f605e080) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 拒绝退货申请消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/ec491a9f-0f5c-35a8-7fdd-1392d4b03c70) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 换货卖家发货消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/a32953b0-7c38-ba85-885b-cad1530ba102) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 售后模块 | 退款成功消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/0654a068-6024-d765-8aa9-f1a0bc58db75) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品上架消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/af96908c-3b9f-ddff-71dd-2d4c479c1d9f) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品下架消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/5009a852-08f7-e2ad-9368-e54f6ea47c33) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品创建消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/7faf1764-0527-0a36-1e2e-6ec322c68097) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品删除恢复消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/afdda85d-e12e-dcab-704b-be15f55293aa) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品删除消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/986efa7f-86b8-73da-196a-41bfa2fee93c) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品审核中止消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/b1bb9fcd-08d1-e1ee-f75b-1c81f0560bda) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品审核通过消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/ae14dcf5-4d4a-2f86-bb0b-a76c3e13dda4) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品审核驳回消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/98920d04-03a4-6230-eaae-7c1a8bc0d197) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品封禁消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/4629ae4d-732c-23da-5335-9da9322891b6) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品提交审核消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/294e4c09-1a51-8c5b-f4b7-cc701e768f30) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品更新消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/cd0b0230-9ebb-33df-81ec-93e56a5b0ff9) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 商品模块 | 商品解除封禁消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/a19ac96b-8994-8ac1-51bf-59eff2b82bd8) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 票务相关 | 出票成功消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/1e4e94e7-aeb5-b5b1-32f8-572293d2c1f4) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 票务相关 | 核销成功消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/e0eb2943-35b6-895e-d60f-670243d432f3) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 票务相关 | 退款成功消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/c5130881-c543-0c0c-8200-39305638e7e4) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 买家修改地址通知 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/a0ddc2fa-e769-dab5-6a4a-042c1e7ce929) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 买家收货信息变更申请消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/1b8d04e4-9cb9-9d2a-5fbf-d940e3cead07) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 发货物流信息变更 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/cf63dfb3-c6fd-2e6a-c2ba-53045e378a9e) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 订单创建消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/3f4f787c-dead-a48f-cf8b-a6c4c254f08a) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 订单发货消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/dd9ae588-af6b-b663-d35e-e5dec7875a3d) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 订单取消消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/0f7d74a3-91f6-faa9-3a47-53ac3b82b770) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 订单备注消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/4e04bf00-dcbc-193c-9a21-74f77fa8ed60) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 订单完成消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/b4a0e16f-42b1-0f43-b650-33a0db7ed040) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 订单支付消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/4ce9f05b-ae93-54c6-0afa-845df6666def) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 订单金额修改消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/85239bc6-20bd-b55b-4227-cefc430bf8a9) |
| 开放能力 / 消息推送 / 推送事件列表 / 交易电商 / 订单模块 | 阶段确认收货消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/06914a21-3200-5f40-1bc6-0b6847d21291) |
| 开放能力 / 消息推送 / 推送事件列表 / 基础授权 | 用户授权 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/5b70f2b6-a7d4-b4b1-6f4f-4170270e4f7a) |
| 开放能力 / 消息推送 / 推送事件列表 / 基础授权 | 解除授权 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/a3f37dde-212b-b71b-5388-fbd3bfb41623) |
| 开放能力 / 消息推送 / 推送事件列表 / 经营号客服 | 关闭消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/065a6aec-a275-2ff4-11ae-54ca55a3b62d) |
| 开放能力 / 消息推送 / 推送事件列表 / 经营号客服 | 消息通知 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/b108e61a-eb85-9057-ccf9-c91c3c50bd54) |
| 开放能力 / 消息推送 / 推送事件列表 / 经营号客服 | 用户进入对话 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/1d3e6f97-feb9-9556-069c-a37509b33a8c) |
| 开放能力 / 消息推送 / 推送事件列表 / 经营号客服 | 留资结果 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/85cd01b5-e1b1-aa5b-cb27-f87b50b7b8f2) |
| 开放能力 / 消息推送 / 推送事件列表 / 视频稿件 | 投稿失败消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/bec4b752-37e3-0049-3a23-e85143d21797) |
| 开放能力 / 消息推送 / 推送事件列表 / 视频稿件 | 投稿开发浏览消息 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/5f4b3ac2-a6b8-cc32-f13b-48e548f5a8ce) |
| 开放能力 / 用户管理 | 查询用户已授权权限列表 | — | https://member.bilibili.com/arcopen/fn/user/account/scopes | [官方文档](https://open.bilibili.com/doc/4/08f935c5-29f1-e646-85a3-0b11c2830558) |
| 开放能力 / 用户管理 | 获取用户union_id | POST | https://member.bilibili.com/arcopen/fn/user/account/union_id | [官方文档](https://open.bilibili.com/doc/4/22e9cc93-1559-f262-0375-bdcefe9257ee) |
| 开放能力 / 用户管理 | 获取用户公开信息 | GET | https://member.bilibili.com/arcopen/fn/user/account/info | [官方文档](https://open.bilibili.com/doc/4/feb66f99-7d87-c206-00e7-d84164cd701c) |
| 开放能力 / 直播能力 | 接入指引 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/19350a57-2e2d-43cf-3e6d-c7de132b24b6) |
| 开放能力 / 直播能力 | 获取直播间基础信息 | GET | https://member.bilibili.com/arcopen/fn/live/room/info | [官方文档](https://open.bilibili.com/doc/4/67eaa648-3f67-f2bc-0fac-efa5fb922305) |
| 开放能力 / 直播能力 | 获取直播间详细信息 | POST | https://member.bilibili.com/arcopen/fn/live/room/detail | [官方文档](https://open.bilibili.com/doc/4/fc6f2a42-506c-52d7-e6a7-fedc11162ee4) |
| 开放能力 / 直播能力 / 开播能力嵌入(一键开播) | 一键开播能力说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/2e018d85-a96e-9deb-dcd6-478fb06cb5b2) |
| 开放能力 / 直播能力 / 开播能力嵌入(一键开播) | 业务流程说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/ddf67fb6-daad-6023-b67a-cc06a28caa4c) |
| 开放能力 / 直播能力 / 开播能力嵌入(一键开播) / 开播接口列表 | 开始直播 | POST | https://member.bilibili.com/liveopen/fn/live/thirdPartyLive/startLive | [官方文档](https://open.bilibili.com/doc/4/cafd6cf4-be34-d2c6-4d43-ca309b7ad346) |
| 开放能力 / 直播能力 / 开播能力嵌入(一键开播) / 开播接口列表 | 开播授权 | GET | https://member.bilibili.com/liveopen/fn/live/thirdPartyLive/grantUrl | [官方文档](https://open.bilibili.com/doc/4/5827c4a4-aab6-235e-624b-a47248d712e3) |
| 开放能力 / 直播能力 / 开播能力嵌入(一键开播) / 开播接口列表 | 授权回调 | POST | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/68757db2-f8bf-eab2-0b09-4bafe1d65264) |
| 开放能力 / 直播能力 / 开播能力嵌入(一键开播) / 开播接口列表 | 结束直播 | POST | https://member.bilibili.com/liveopen/fn/live/thirdPartyLive/endLive | [官方文档](https://open.bilibili.com/doc/4/e84cd5ba-68fe-effe-1835-c2a2ff22a72a) |
| 开放能力 / 直播能力 / 消息发送 | 发送弹幕 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/d1276f50-2401-9202-9b63-097f63343e04) |
| 开放能力 / 直播能力 / 直播视频流相关 | 获取直播间流信息 | POST | https://member.bilibili.com/arcopen/fn/live/room/stream | [官方文档](https://open.bilibili.com/doc/4/73330581-9bd7-1177-f2b2-64f1fc44a52f) |
| 开放能力 / 直播能力 / 直播间长连和消息 | 直播房间批量长链心跳 | POST | https://member.bilibili.com/arcopen/fn/live/room/ws-batch-heartbeat | [官方文档](https://open.bilibili.com/doc/4/6ea09a64-8ac2-b650-9580-866850432c2c) |
| 开放能力 / 直播能力 / 直播间长连和消息 | 直播房间长链信息及心跳ID | POST | https://member.bilibili.com/arcopen/fn/live/room/ws-start | [官方文档](https://open.bilibili.com/doc/4/da2b13dc-7f7a-0025-be11-0b677e793baa) |
| 开放能力 / 直播能力 / 直播间长连和消息 | 直播房间长链心跳 | POST | https://member.bilibili.com/arcopen/fn/live/room/ws-heartbeat | [官方文档](https://open.bilibili.com/doc/4/8f57c906-15e6-4e61-e850-da0911be1cf1) |
| 开放能力 / 直播能力 / 直播间长连和消息 | 直播间消息websocket协议 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/5cac94fe-57f9-06db-7515-523d81c44f85) |
| 开放能力 / 直播能力 / 直播间长连和消息 | 长连CMD说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/c7b549c9-d5d6-0331-b510-465ed4107e01) |
| 开放能力 / 站内版权授权曲库 | 用前须知 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/4a2b8e0c-ae97-a0dc-c3b2-01a1726dc587) |
| 开放能力 / 站内版权授权曲库 / 接口列表 | 搜索媒体信息 | POST | https://member.bilibili.com/arcopen/fn/music/search | [官方文档](https://open.bilibili.com/doc/4/4a81f458-998f-ebf2-6311-93b460c60481) |
| 开放能力 / 站内版权授权曲库 / 接口列表 | 获取媒体元数据 | POST | https://member.bilibili.com/arcopen/fn/music/meta/list | [官方文档](https://open.bilibili.com/doc/4/2b9b8c6a-3b79-8190-4722-a5237aa51ea4) |
| 开放能力 / 站内版权授权曲库 / 接口列表 | 获取媒体资源信息 | POST | https://member.bilibili.com/arcopen/fn/music/list | [官方文档](https://open.bilibili.com/doc/4/6bcee156-df92-d0e7-e683-b536f7030661) |
| 开放能力 / 经营号客服 | 服务说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/4256a5c5-25ee-13a6-9915-14b2fb0da083) |
| 开放能力 / 经营号客服 / 接口文档 | 上传图片 | POST | https://member.bilibili.com/arcopen/fn/market/customer/image_upload | [官方文档](https://open.bilibili.com/doc/4/5083729f-bf45-c07e-a4f4-e5a08728bb53) |
| 开放能力 / 经营号客服 / 接口文档 | 修改客服状态 | POST | https://member.bilibili.com/arcopen/fn/market/customer/conversation/staff_status_update | [官方文档](https://open.bilibili.com/doc/4/ebd4bb62-5428-7570-680d-bc317abebb82) |
| 开放能力 / 经营号客服 / 接口文档 | 关闭会话 | POST | https://member.bilibili.com/arcopen/fn/market/customer/conversation/close | [官方文档](https://open.bilibili.com/doc/4/74d14e64-28cf-eb60-4429-d7d605a22e85) |
| 开放能力 / 经营号客服 / 接口文档 | 发送消息 | POST | https://member.bilibili.com/arcopen/fn/market/customer/conversation/send_msg | [官方文档](https://open.bilibili.com/doc/4/2e315f1f-6879-0c1f-304b-937b3462e3d7) |
| 开放能力 / 经营号客服 / 接口文档 | 获取用户来源 | POST | https://member.bilibili.com/arcopen/fn/market/customer/conversation/user_from | [官方文档](https://open.bilibili.com/doc/4/1b6cbc70-ddea-03ee-d176-5755f61959dc) |
| 开放能力 / 经营号客服 / 接口文档 | 获客工具列表查询 | POST | https://member.bilibili.com/arcopen/fn/market/customer/conversation/acquisition_tool_list | [官方文档](https://open.bilibili.com/doc/4/7a5de48a-93ba-a0ea-9355-0fc7fa366688) |
| 开放能力 / 视频稿件管理 | 视频稿件删除 | POST | https://member.bilibili.com/arcopen/fn/archive/delete | [官方文档](https://open.bilibili.com/doc/4/23d78390-4119-1e5f-2bbe-b45bd5cecdb0) |
| 开放能力 / 视频稿件管理 | 视频稿件编辑 | POST | https://member.bilibili.com/arcopen/fn/archive/edit | [官方文档](https://open.bilibili.com/doc/4/ddfbe54d-b4ab-340e-c698-933b9a3c619c) |
| 开放能力 / 视频稿件管理 / 服务端视频稿件投递 | 分区查询 | GET | https://member.bilibili.com/arcopen/fn/archive/type/list | [官方文档](https://open.bilibili.com/doc/4/4f13299b-5316-142f-df6a-87313eaf85a9) |
| 开放能力 / 视频稿件管理 / 服务端视频稿件投递 | 单个小视频文件上传 | POST | https://openupos.bilivideo.com/video/v2/upload | [官方文档](https://open.bilibili.com/doc/4/f22a0eee-c92d-0f1d-f69c-be170cf533c7) |
| 开放能力 / 视频稿件管理 / 服务端视频稿件投递 | 封面上传 | POST | https://member.bilibili.com/arcopen/fn/archive/cover/upload | [官方文档](https://open.bilibili.com/doc/4/8243399e-50e3-4058-7f01-1ebe4c632cf8) |
| 开放能力 / 视频稿件管理 / 服务端视频稿件投递 | 接口概览 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/1c4302da-8171-d036-5400-ca0dec077045) |
| 开放能力 / 视频稿件管理 / 服务端视频稿件投递 | 文件上传预处理 | POST | https://member.bilibili.com/arcopen/fn/archive/video/init | [官方文档](https://open.bilibili.com/doc/4/0c532c6a-e6fb-0aff-8021-905ae2409095) |
| 开放能力 / 视频稿件管理 / 服务端视频稿件投递 | 文件分片上传 | POST | https://openupos.bilivideo.com/video/v2/part/upload | [官方文档](https://open.bilibili.com/doc/4/733a520a-c50f-7bb4-17cb-35338ba20500) |
| 开放能力 / 视频稿件管理 / 服务端视频稿件投递 | 文件分片合片 | POST | https://member.bilibili.com/arcopen/fn/archive/video/complete | [官方文档](https://open.bilibili.com/doc/4/0828e499-38d8-9e58-2a70-a7eaebf9dd64) |
| 开放能力 / 视频稿件管理 / 服务端视频稿件投递 | 视频稿件提交 | POST | https://member.bilibili.com/arcopen/fn/archive/add-by-utoken | [官方文档](https://open.bilibili.com/doc/4/f7fc57dd-55a1-5cb1-cba4-61fb2994bf0f) |
| 开放能力 / 视频稿件管理 / 用户端唤起粉端投稿 | 业务说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/58749206-f792-f442-9824-1d5f941633c3) |
| 开放能力 / 视频稿件管理 / 用户端唤起粉端投稿 | 唤起粉端投稿接口说明 | POST | https://member.bilibili.com/arcopen/fn/resource/add_share | [官方文档](https://open.bilibili.com/doc/4/8b825dee-e49e-5843-7e80-f289b878076a) |
| 开放能力 / 视频稿件管理 / 视频稿件查询 | 查询单一视频稿件详情 | GET | https://member.bilibili.com/arcopen/fn/archive/view | [官方文档](https://open.bilibili.com/doc/4/d9554788-dcef-f139-6217-b487d41c3826) |
| 开放能力 / 视频稿件管理 / 视频稿件查询 | 查询用户视频稿件列表 | GET | https://member.bilibili.com/arcopen/fn/archive/viewlist | [官方文档](https://open.bilibili.com/doc/4/a24030b7-6b8f-b36c-32d8-a4aae67fcc35) |
| 开放能力 / 课堂业务 | 服务说明 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/7e45bbb0-1fce-9561-06b4-3b2f6c2d61a4) |
| 开放能力 / 课堂业务 / 接口 | 学员看课明细 | — | https://member.bilibili.com/arcopen/fn/common/student_study_progress_detail | [官方文档](https://open.bilibili.com/doc/4/447ee224-3220-2e65-6228-4d7793212d18) |
| 开放能力 / 课堂业务 / 接口 | 学员看课进度列表 | — | https://member.bilibili.com/arcopen/fn/common/student_study_progress_list | [官方文档](https://open.bilibili.com/doc/4/7019cf12-4f01-78d2-088c-faafe4a113b3) |
| 开放能力 / 课堂业务 / 接口 | 订单号查询订单信息 | POST | https://member.bilibili.com/arcopen/fn/common/by_orderno_for_course_order | [官方文档](https://open.bilibili.com/doc/4/63a46da0-bbaa-f048-fda7-d70ce1382486) |
| 接入指引 | Android应用接入 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/1f1cd948-de8f-6a9f-3b9c-2cb484da3cbb) |
| 接入指引 | IOS应用接入 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/67901da7-ffab-1be0-f615-c0138ce974a5) |
| 接入指引 | SDK信息收集告知表 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/6793c7b3-8d08-2368-7c0f-c60592eee6b6) |
| 接入指引 | 网页应用接入 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/aac73b2e-4ff2-b75c-4c96-35ced865797b) |
| 新手指引 | 入驻 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/cbdcee3b-f57e-5c7b-cf27-83892fb811c4) |
| 新手指引 | 平台简介 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/aa909d41-01da-e47e-e64c-f32bc76b8a42) |
| 新手指引 | 应用管理 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/7702bf71-673f-8085-e93f-2014917e0da7) |
| 运营指南 | 处罚公告 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/2f361c1e-72f0-36f0-3e68-093b730b57e6) |
| 运营指南 | 处罚规则 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/1fb5cc0b-3404-9354-66fe-b8b4b0428887) |
| 运营指南 | 联系我们 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/e9a4bc66-473c-3a32-2658-db94ae6513fe) |
| 运营指南 | 运营规范 | — | 说明/回调/无生产 URL | [官方文档](https://open.bilibili.com/doc/4/6b917ce7-f2d6-57b8-57df-cf0887540cef) |
