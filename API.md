# 校园墙小程序 - 后端 API 接口文档

## 基础信息

- **服务端口**: 80
- **数据库**: SQLite（零依赖，无需安装）
- **认证方式**: 微信授权登录 + JWT Token
- **Base URL**: `http://your-domain/api`

## 微信授权登录流程

```
小程序前端                    后端服务器                    微信API
    |                            |                          |
    |--- wx.login() 获取 code -->|                          |
    |                            |--- GET sns/jscode2session-->
    |                            |<-- openid + session_key --|
    |                            |                          |
    |                            | 查找/创建用户             |
    |                            | 生成 JWT token            |
    |<-- access_token + user ----|                          |
```

---

## API 接口列表

### 1. 系统接口

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/` | 否 | 服务信息 |
| GET | `/health` | 否 | 健康检查 |

---

### 2. 认证模块 `/api/auth`

#### 2.1 微信登录
```
POST /api/auth/wx-login
```
**认证**: 不需要
**请求体**:
```json
{
  "code": "wx.login()获取的临时凭证",
  "nickname": "用户昵称",
  "avatar_url": "头像URL",
  "gender": 0,
  "school": "学校名称"
}
```
**响应**:
```json
{
  "code": 200,
  "message": "login success",
  "data": {
    "access_token": "eyJ...",
    "user": {
      "id": 1,
      "nickname": "校园同学",
      "avatar_url": "",
      "school": "",
      "level": 1,
      "exp": 0,
      "post_count": 0,
      "role": 0
    }
  }
}
```

> **开发模式**: `WECHAT_APPID` 以 `wx_test_` 开头时，跳过微信API，直接用 code 作为 openid

#### 2.2 获取用户信息
```
GET /api/auth/profile
```
**认证**: 需要 Bearer Token
**响应**:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "nickname": "校园同学",
    "avatar_url": "",
    "gender": 0,
    "school": "",
    "level": 1,
    "exp": 0,
    "post_count": 0,
    "like_received_count": 0,
    "comment_received_count": 0,
    "show_contact": 0,
    "contact_info": "",
    "role": 0,
    "created_at": "2026-06-21T10:00:00"
  }
}
```

#### 2.3 更新用户信息
```
PUT /api/auth/profile
```
**认证**: 需要 Bearer Token
**请求体** (所有字段可选):
```json
{
  "nickname": "新昵称",
  "school": "新学校",
  "show_contact": 1,
  "contact_info": "联系方式",
  "gender": 1
}
```

---

### 3. 帖子模块 `/api/posts`

#### 3.1 获取帖子列表
```
GET /api/posts/?page=1&per_page=20&category_id=1&order_by=latest
```
**认证**: 可选（登录后返回 is_liked 字段）
**参数**:
- `page`: 页码，默认 1
- `per_page`: 每页数量，默认 20
- `category_id`: 分区ID筛选
- `order_by`: 排序方式 `latest`(最新) / `hot`(最热)

#### 3.2 获取帖子详情
```
GET /api/posts/<post_id>
```
**认证**: 可选

#### 3.3 发布帖子
```
POST /api/posts/
```
**认证**: 需要 Bearer Token
**请求体**:
```json
{
  "title": "帖子标题",
  "content": "帖子内容",
  "category_id": 1,
  "images": ["url1", "url2"],
  "video_url": "",
  "is_anonymous": 0
}
```

#### 3.4 搜索帖子
```
GET /api/posts/search?q=关键词&category_id=1&page=1
```
**认证**: 可选
**参数**:
- `q`: 搜索关键词（必填）
- `category_id`: 分区筛选
- `page`: 页码

#### 3.5 点赞/取消点赞
```
POST /api/posts/<post_id>/like
```
**认证**: 需要 Bearer Token

#### 3.6 获取分区列表
```
GET /api/posts/categories
```
**认证**: 不需要

---

### 4. 评论模块 `/api/comments`

#### 4.1 发表评论
```
POST /api/comments/
```
**认证**: 需要 Bearer Token
**请求体**:
```json
{
  "post_id": 1,
  "content": "评论内容",
  "parent_id": null,
  "reply_to_user_id": null
}
```

#### 4.2 获取评论列表
```
GET /api/comments/<post_id>/comments?page=1&per_page=20
```
**认证**: 可选

---

### 5. 用户模块 `/api/users`

#### 5.1 获取用户资料
```
GET /api/users/profile
```
**认证**: 需要 Bearer Token

#### 5.2 获取用户发布的帖子
```
GET /api/users/<user_id>/posts?page=1&per_page=20
```
**认证**: 可选

#### 5.3 获取用户点赞的帖子
```
GET /api/users/<user_id>/likes?page=1&per_page=20
```
**认证**: 需要 Bearer Token（仅自己可看）

#### 5.4 获取等级配置
```
GET /api/users/level-config
```
**认证**: 不需要

#### 5.5 获取数据统计
```
GET /api/users/me/statistics
```
**认证**: 需要 Bearer Token

---

### 6. 上传模块 `/api/upload`

#### 6.1 上传图片
```
POST /api/upload/image
```
**认证**: 需要 Bearer Token
**请求体**: `multipart/form-data`
- `file`: 图片文件

---

### 7. 管理后台 `/api/admin`

#### 7.1 获取待审核帖子
```
GET /api/admin/posts/pending?page=1&per_page=20
```
**认证**: 需要 Bearer Token + 管理员权限

#### 7.2 审核帖子
```
PUT /api/admin/posts/<post_id>/review
```
**认证**: 需要 Bearer Token + 管理员权限
**请求体**:
```json
{
  "action": "approve",
  "reason": ""
}
```

#### 7.3 管理后台数据概览
```
GET /api/admin/dashboard/stats
```
**认证**: 需要 Bearer Token + 管理员权限

#### 7.4 获取关键词列表
```
GET /api/admin/keywords/?page=1&per_page=50&category=default
```
**认证**: 需要 Bearer Token + 管理员权限

#### 7.5 添加关键词
```
POST /api/admin/keywords/
```
**认证**: 需要 Bearer Token + 管理员权限
**请求体**:
```json
{
  "keyword": "敏感词",
  "category": "default",
  "level": 1
}
```
> level: 1=警告(人工审核), 2=拒绝(自动拒绝)

#### 7.6 批量添加关键词
```
POST /api/admin/keywords/batch
```
**认证**: 需要 Bearer Token + 管理员权限
**请求体**:
```json
{
  "keywords": "关键词1\n关键词2\n关键词3",
  "category": "default",
  "level": 1
}
```

#### 7.7 删除关键词
```
DELETE /api/admin/keywords/<kw_id>
```
**认证**: 需要 Bearer Token + 管理员权限

#### 7.8 数据统计概览
```
GET /api/admin/stats/overview
```
**认证**: 需要 Bearer Token

---

## 认证方式

除标注"不需要认证"的接口外，所有接口需要在 Header 中携带 JWT Token:

```
Authorization: Bearer <access_token>
```

---

## 默认数据

### 分区列表
| ID | 名称 | 图标 |
|----|------|------|
| 1 | 失物招领 | 🔍 |
| 2 | 借东西 | 📦 |
| 3 | 竞赛组队 | 🏆 |
| 4 | 约球 | ⚽ |
| 5 | 社团通知 | 📢 |
| 6 | 表白墙 | 💕 |
| 7 | 吹水闲聊 | 💬 |

### 等级配置
| 等级 | 称号 | 所需经验 |
|------|------|----------|
| 1 | 校园新生 | 0 |
| 2 | 活跃达人 | 100 |
| 3 | 热心学长 | 300 |
| 4 | 校园KOL | 600 |
| 5 | 风云人物 | 1000 |
| 6 | 传奇校草 | 2000 |
| 7 | 校园传说 | 5000 |
