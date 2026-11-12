# B站视频笔记接口：授权实测

日期：2026-11-12（北京时间）  
目标：用户授权的公开视频（具体标识已省略）  
依据：[B站视频页第一方笔记脚本](https://s1.hdslb.com/bfs/seed/jinkela/material/bilinote.umd.min.js)和授权操作中的保存、发布、回读。

## 读写接口

| 操作 | 方法与路径（api.bilibili.com） | 关键参数 / 结果 | 验证 |
| --- | --- | --- | --- |
| 判断是否可记笔记 | GET /x/note/is_forbid | query: aid；data.forbid_note_entrance | 实测 false |
| 当前用户在视频下的笔记 | GET /x/note/list/archive | query: oid=视频 aid,oid_type=0,csrf；data.noteIds | 新建前为空，保存后有 note_id |
| 读取个人笔记 | GET /x/note/info | query: oid,oid_type,note_id,csrf；data.title,content,summary,pub_status,pub_reason | 保存和发布后均回读成功 |
| 上传笔记图片 | POST /x/note/image/upload | multipart: file,csrf；data.location 为可嵌入图片地址 | 实测 code=0 |
| 保存私人笔记 | POST /x/note/add | form: from=save,oid,oid_type,note_id（新建为空）,title,summary,content,tags,cls=1,csrf,cont_len,hash,platform=web；data.note_id | 实测 code=0，回读 pub_status=0 |
| 提交公开审核 | POST /x/note/add | 在保存字段上加已保存 note_id,publish=1,original=1,auto_comment=0,comment_format=2 | 实测 code=0，随后 pub_status 从 1 变为 2 |
| 公开笔记列表 | GET /x/note/publish/list/archive | query: oid,oid_type,pn,ps,uper_mid=视频 UP 主 mid；data.list[] 含 cvid,web_url,author.mid | 审核通过后查到本次 cvid |
| 读取公开笔记 | GET /x/note/publish/info | query: cvid；data.content,pub_status,note_id 等 | 登录态与匿名请求均 code=0、pub_status=2 |

## 正文与图片格式

- content 是 Quill Delta op 数组序列化后的 JSON 字符串。普通文本使用 insert 字符串；图片使用 insert.imageUpload 对象，字段有 id、source、status、url、width。
- 图片 url 使用上传接口返回的 data.location。本次返回的是 api.bilibili.com 的 /x/note/image 路径；公开笔记仍正确显示导图。不要猜测或硬编码图片 CDN 地址。
- cont_len 对应编辑器内容长度，图片算一个字符；hash 是页面初始化时的毫秒时间戳；summary 从正文生成或单独传入；没有时间标签时 tags 可为空字符串。
- 本次时间锚点写成普通文本。若用编辑器的时间标签，tags 需要与正文中的标签对应。
- auto_comment=0 用于关闭笔记发布时的自动评论。HTTP 200 和业务 code=0 只表示请求被接受；是否公开可见还要检查 pub_status 与公开读取。

## 状态与本次结果

第一方脚本的状态分类：0 未公开；1/5 审核中；2 审核通过；3/4/6 未通过，原因看 pub_reason。

公开笔记页面已在无登录浏览器中显示正文和思维导图；公开信息接口也可匿名读取。笔记 ID、cvid 与视频标识已省略。接口记录不包含 Cookie、csrf 值、图片上传临时地址或请求签名。

完整业务目录见 [B站全站接口目录](./api-catalog.md)。
