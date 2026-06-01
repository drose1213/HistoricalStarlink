# 历史星链探索 — 功能模块全景图

> **技术栈**: Vue 3 + TypeScript + Pinia + FastAPI + SQLAlchemy + MySQL/SQLite + Redis  
> **服务器**: `111.231.50.67`  
> **最后更新**: 2026-06-01

---

## 一、系统架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Vue 3 + Vite)                    │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  │首页   │ │事件   │ │对话   │ │个人   │ │卡牌   │ │排行   │ │
│  │Home  │ │Detail│ │Dialogue│ │Profile│ │Champion│ │Leader │ │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ │
│     └────────┴────────┴────────┴────────┴────────┘     │
│                    Pinia Stores + API Layer               │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (JWT Bearer)
┌────────────────────────┴────────────────────────────────┐
│                  后端 (FastAPI + Python)                   │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  │Auth  │ │Dialogue│ │Explore│ │Vote  │ │Rating│ │Champion│ │
│  │Signature│ │Events │ │RAG  │ │Config│ └──────┘ └──────┘ │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ │
│     └────────┴────────┴────────┴────────┴────────┘     │
│              SQLAlchemy ORM + Redis Cache                  │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │ MySQL (优先/强制)     │
              │ SQLite (自动回退)     │
              └─────────────────────┘
```

---

## 二、路由与页面结构

### 前端路由 (Hash 模式)

| 路径 | 页面组件 | 功能 | 需要登录 |
|------|---------|------|---------|
| `/` | HomeView | 首页宇宙星图 | ❌ |
| `/event/:id` | EventDetailView | 事件详情+星链 | ❌ |
| `/dialogue/:eventId` | DialogueExplorer | 时空对话 | ✅ |
| `/profile` | ProfileView | 个人中心 | ✅ |
| `/explore` | → `/profile?tab=explore` | 探索记录 | ✅ |
| `/trends` | → `/profile?tab=trends` | 趋势分析 | ✅ |
| `/champions` | ChampionsView | 卡牌展馆 | ❌ |
| `/leaderboard` | LeaderboardView | 探索排行榜 | ❌ |
| `/login` | AuthView | 登录/注册 | ❌ |

### 导航栏结构

```
首页 ─ 卡牌 ─ 排行 ─ [个人中心] (登录后) / [登录] (未登录)
```

---

## 三、功能模块详解

### 模块 1: 认证系统 (`auth`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/auth.py`, `frontend/src/views/AuthView.vue`, `frontend/src/stores/auth.ts`

#### 功能
- 邮箱验证码发送 + 60秒冷却 + 每小时10次限制
- 用户注册（用户名+邮箱+验证码+密码）
- 用户登录（用户名/邮箱+密码）
- JWT Token 鉴权（7天有效期）
- 邮件模板（赛博朋克风格HTML）

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/send-code` | 发送邮箱验证码 |
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| PUT | `/api/auth/profile` | 更新用户资料 |

#### 登录保护
- `requireAuth()` 函数：所有探索操作（开始探索、对话、投票、评分）前调用
- 未登录时弹出提示并跳转登录页

---

### 模块 2: 宇宙星图首页 (`home`)

**状态**: ✅ 已完成  
**文件**: `frontend/src/views/HomeView.vue`, `frontend/src/components/CosmicMap.vue`

#### 功能
- Canvas 星空背景（250颗闪烁星星）
- SVG 星座连线（东方青色/西方粉色/跨文明金色虚线）
- 50个历史事件星节点（可点击跳转详情）
- 星云雾气效果
- 左侧抽屉式事件列表（可展开/收起）
- 底部搜索栏（关键词搜索历史事件）
- 区域筛选（全部/东方/西方）

---

### 模块 3: 事件详情 (`event-detail`)

**状态**: ✅ 已完成  
**文件**: `frontend/src/views/EventDetailView.vue`, `frontend/src/components/StarlinkPlanets.vue`

#### 功能
- 星链行星可视化（SVG 弧形曲线+发光效果）
- 中心行星 = 当前事件
- 左侧：历史原因关联事件（可展开描述）
- 右侧：历史影响关联事件（可展开描述）
- 飞船传送动画（点击关联行星→1.5秒加载→跳转新事件）
- 点击关联行星跳转详情

#### 数据结构
```typescript
interface HistoryEvent {
  id: string
  name: string
  year: number
  region: 'china' | 'foreign'
  importance: number
  description: string
  causes: string[]
  consequences: string[]
  related_concepts: string[]
  figures: string[]
  tags: string[]
  related?: {
    causes: Array<{ id: string; weight: number }>
    consequences: Array<{ id: string; weight: number }>
  }
}
```

#### 50 个历史事件（数据库 seed 数据）

**中国历史事件（26个）**:
长城修建(-221) → 造纸术发明(105) → 火药发明(850) → 指南针发明(1100) → 印刷术发明(1040)  
商鞅变法(-356) → 秦统一六国(-221) → 汉朝建立(-202)  
丝绸之路(-130) → 海上丝绸之路(200)  
唐朝盛世(618) → 安史之乱(755)  
宋朝科技文化(960) → 宋朝商业繁荣(960)  
蒙古帝国(1206) → 郑和下西洋(1405)  
鸦片战争(1840) → 太平天国运动(1851) → 洋务运动(1861) → 戊戌变法(1898)  
辛亥革命(1911) → 五四运动(1919) → 红军长征(1934) → 新中国成立(1949) → 改革开放(1978)

**世界历史事件（19个）**:
亚历山大东征(-334) → 罗马帝国建立(-27) → 西罗马帝国灭亡(476)  
十字军东征(1096) → 黑死病(1347) → 文艺复兴(1400) → 宗教改革(1517)  
光荣革命(1688) → 科学革命(1543) → 启蒙运动(1685)  
美国独立(1776) → 法国大革命(1789) → 工业革命(1760)  
一战(1914) → 二战(1939) → 冷战(1947) → 柏林墙倒塌(1989)  
互联网诞生(1969) → 人类登月(1969)  
废除奴隶制(1833) → 明治维新(1868) → 美国内战(1861) → 日本废藩置县(1871)  
包豪斯学院(1919) → 法属印度支那(1887)

---

### 模块 4: 时空对话 (`dialogue`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/dialogue.py`, `backend/dialogue_engine.py`, `frontend/src/components/DialogueExplorer.vue`, `frontend/src/stores/dialogue.ts`

#### 功能
- 预置剧本对话（每个事件有独立 NPC 角色）
- 多轮对话（选择+自由文本）
- 时间线分支（选择影响结局）
- 打字动画效果
- 结局面板（历史定论/平行时间线）
- 对话历史记录

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/dialogue/start` | 开始对话 |
| POST | `/api/dialogue/choice` | 发送选择 |
| POST | `/api/dialogue/chat` | 自由文本 |
| GET | `/api/dialogue/records` | 对话记录列表 |
| GET | `/api/dialogue/events` | 可用对话事件 |
| GET | `/api/dialogue/{id}` | 对话详情 |
| DELETE | `/api/dialogue/{id}` | 删除对话 |

---

### 模块 5: 探索记录 (`exploration`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/exploration.py`, `frontend/src/components/ExplorationRecord.vue`, `frontend/src/stores/exploration.ts`

#### 功能
- 开始/结束探索（记录时长）
- 探索历史列表
- 统计信息（总次数、事件数、时长）
- 实时计时器

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/exploration/start` | 开始探索 |
| POST | `/api/exploration/end` | 结束探索 |
| GET | `/api/exploration/records` | 探索记录列表 |
| GET | `/api/exploration/records/{id}` | 单条记录 |
| GET | `/api/exploration/event/{event_id}` | 事件探索记录 |
| GET | `/api/exploration/stats` | 统计信息 |
| DELETE | `/api/exploration/records/{id}` | 删除记录 |

---

### 模块 6: 投票系统 (`vote`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/vote.py`, `frontend/src/components/VotingSystem.vue`, `frontend/src/stores/vote.ts`

#### 功能
- 三种投票：赞同(1)、反对(-1)、收藏(1)
- 投票统计（条形图展示）
- 支持切换/取消投票
- 热门事件排行

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/vote` | 创建/切换投票 |
| GET | `/api/vote/stats/{event_id}` | 投票统计 |
| GET | `/api/vote/my` | 用户投票记录 |
| GET | `/api/vote/batch-stats` | 批量统计 |

---

### 模块 7: 评分系统 (`rating`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/rating.py`, `frontend/src/components/RatingSystem.vue`, `frontend/src/stores/rating.ts`

#### 功能
- 5星评分 + 文字评价
- 平均分统计
- 评分列表展示
- 支持修改评分

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/rating` | 创建评分 |
| PUT | `/api/rating/{id}` | 更新评分 |
| GET | `/api/rating` | 评分列表 |
| GET | `/api/rating/stats/{event_id}` | 评分统计 |
| DELETE | `/api/rating/{id}` | 删除评分 |

---

### 模块 8: 冠军卡牌 (`champion`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/champion.py`, `frontend/src/views/ChampionsView.vue`, `frontend/src/components/ChampionCard.vue`, `frontend/src/stores/champion.ts`

#### 功能
- 卡牌解锁/获取
- 按稀有度分类（传说/史诗/稀有/普通）
- 全服排行展示（每稀有度前三名）
- 卡牌属性网格
- 拥有者信息

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/champion` | 创建/更新卡牌 |
| GET | `/api/champion` | 卡牌列表 |
| GET | `/api/champion/stats/{session_id}` | 用户统计 |
| PUT | `/api/champion/{id}` | 更新卡牌 |
| DELETE | `/api/champion/{id}` | 删除卡牌 |

---

### 模块 9: 个人中心 (`profile`)

**状态**: ✅ 已完成  
**文件**: `frontend/src/views/ProfileView.vue`

#### 功能
- 三 Tab 切换（探索记录/趋势分析/我的卡牌）
- URL 参数支持（`?tab=explore|trends|cards`）
- 未登录自动跳转登录页
- 趋势分析：区域分布、兴趣维度、时间线
- 我的卡牌：用户卡牌收藏网格

---

### 模块 10: 排行榜 (`leaderboard`)

**状态**: ✅ 已完成  
**文件**: `frontend/src/views/LeaderboardView.vue`

#### 功能
- 时间段切换（每日/每周/每月/每年）
- 前三名领奖台
- 排名表格
- 热门事件排行

---

### 模块 11: 签名上传 (`signature`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/signature.py`, `frontend/src/components/SignatureUpload.vue`, `frontend/src/stores/signature.ts`

#### 功能
- 拖拽/点击上传图片（JPG/PNG，5MB）
- 图片预览 + 进度条
- 签名列表管理

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/signature/upload` | 上传签名 |
| GET | `/api/signature` | 签名列表 |
| GET | `/api/signature/{id}` | 单条签名 |
| DELETE | `/api/signature/{id}` | 删除签名 |

---

### 模块 12: 历史事件 API (`events`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/events.py`, `backend/models/event.py`, `backend/data/events_data.py`

#### 功能
- 数据库存储的事件数据（50 个中外历史事件）
- 启动时自动 seed 到 `history_events` 表
- 支持区域筛选（china/foreign）
- 支持标签筛选和关键词搜索
- 分页查询

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/events` | 获取事件列表（支持筛选+分页） |
| GET | `/api/events/search?q=xxx` | 搜索事件 |
| GET | `/api/events/{event_id}` | 获取单个事件详情 |

---

### 模块 13: RAG 知识库 (`rag`)

**状态**: ✅ 后端完成（需要 MiniMax API Key 才能使用 AI 功能）  
**文件**: `backend/routers/rag.py`, `backend/rag_engine.py`

#### 功能
- 基于 MiniMax API 的向量嵌入检索（embedding mode）
- 无 API Key 时自动降级为关键词匹配模式（keyword mode）
- RAG 智能问答（基于检索结果 + MiniMax Chat API 生成回答）
- 索引重建接口

#### 双模式降级
| 条件 | 搜索模式 | 问答模式 |
|------|---------|---------|
| 配置了 MINIMAX_API_KEY | 向量语义搜索 | MiniMax Chat API |
| 未配置 API Key | 关键词匹配 | 本地模板回答 |

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/rag/search` | 搜索相关历史事件 |
| POST | `/api/rag/ask` | RAG 智能问答 |
| POST | `/api/rag/rebuild` | 重建 RAG 索引 |

---

### 模块 14: 系统配置 (`config`)

**状态**: ✅ 已完成  
**文件**: `backend/routers/config.py`, `backend/models/system_config.py`, `backend/data/config_data.py`

#### 功能
- 数据库存储系统配置（35 项默认配置）
- 支持分组查看（app/database/redis/cors/security/email/upload/ai）
- 支持按 Key 查询和批量更新
- 配置修改后自动热加载到运行时 Settings
- 启动时自动 seed 默认配置

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config` | 获取所有配置（可按分组筛选） |
| GET | `/api/config/groups` | 获取所有配置分组 |
| GET | `/api/config/{key}` | 获取单个配置 |
| PUT | `/api/config` | 批量更新配置 |
| PUT | `/api/config/{key}` | 更新单个配置 |

---

## 四、数据库自动初始化

### 启动时自动执行

应用启动时通过 FastAPI lifespan 执行以下初始化流程：

```
lifespan.start
  ├─ init_db()              → 创建所有表（Base.metadata.create_all）
  ├─ _seed_configs()        → 写入 35 项默认系统配置（首次启动）
  ├─ load_db_config_safe()  → 从数据库加载配置到运行时
  └─ _seed_events()         → 写入 50 个历史事件（首次启动）
```

**关键修复**: `database.py` 中 `from . import models` 确保所有 ORM 模型在 `create_all` 前已注册到 `Base.metadata`，否则表不会被创建。

---

## 五、数据库选择策略

数据库通过 `DB_DRIVER` 环境变量控制：

| `DB_DRIVER` 值 | 行为 | 适用场景 |
|---|---|---|
| `auto`（默认） | TCP 探测 MySQL，连上用 MySQL，连不上自动降级 SQLite | 开发/测试 |
| `mysql` | 强制使用 MySQL | 生产环境 |
| `sqlite` | 强制使用 SQLite | 本地开发 |

**注意**: 生产环境建议设为 `mysql`，避免因 MySQL 临时不可用而静默降级到 SQLite。两种数据库的数据完全隔离。

---

## 六、部署配置

### 快速启动（本地开发）

```bash
# 1. 进入项目根目录
cd HistoricalStarlink

# 2. 启动所有服务（一键脚本）
.\start.ps1

# 或手动启动：
# 后端
python -m venv venv
.\venv\Scripts\pip install -r backend\requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### Docker Compose 部署（生产环境）

```bash
# 启动全部服务
docker-compose up -d

# 服务组件
# - mysql:8.0       → 数据库（端口 3306）
# - redis:7-alpine   → 缓存（端口 6379）
# - backend          → FastAPI 后端（端口 8000）
# - frontend         → Vue 3 前端
# - nginx:alpine     → 反向代理（端口 80）
```

### 环境变量配置 (.env)

```env
# === 数据库 ===
DB_DRIVER=auto            # auto/mysql/sqlite
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=historical_starlink

# === Redis（可选） ===
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# === 服务器 ===
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false

# === JWT ===
JWT_SECRET_KEY=your_secret_key

# === 邮件（QQ邮箱 SMTP） ===
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_smtp_authorization_code
SMTP_FROM=your_email@qq.com

# === CORS ===
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# === MiniMax API（RAG 知识库，可选） ===
MINIMAX_API_KEY=your_api_key
```

### 服务健康检查

```
GET /health → 数据库连接状态 + Redis 连接状态
GET /       → 应用名称、版本、运行状态
GET /docs  → Swagger API 文档
```

---

## 七、文件结构索引

```
HistoricalStarlink/
├── frontend/
│   └── src/
│       ├── views/              # 页面组件
│       │   ├── HomeView.vue           # 首页
│       │   ├── EventDetailView.vue    # 事件详情
│       │   ├── ProfileView.vue        # 个人中心
│       │   ├── ChampionsView.vue      # 卡牌展馆
│       │   ├── LeaderboardView.vue    # 排行榜
│       │   ├── ExploreView.vue        # 探索记录(旧)
│       │   ├── TrendsView.vue         # 趋势分析(旧)
│       │   └── AuthView.vue           # 登录/注册
│       ├── components/         # 可复用组件
│       │   ├── CosmicMap.vue          # 宇宙星图
│       │   ├── StarlinkPlanets.vue    # 星链行星
│       │   ├── DialogueExplorer.vue   # 时空对话
│       │   ├── ExplorationRecord.vue  # 探索记录
│       │   ├── VotingSystem.vue       # 投票系统
│       │   ├── RatingSystem.vue       # 评分系统
│       │   ├── ChampionCard.vue       # 卡牌展示
│       │   └── SignatureUpload.vue    # 签名上传
│       ├── stores/             # Pinia Store
│       ├── api/                # API 模块
│       ├── data/
│       │   └── events.ts       # 共享事件数据（前端关系映射）
│       ├── utils/              # 工具函数
│       ├── types/              # TypeScript 类型定义
│       └── router/             # 路由配置
├── backend/
│   ├── main.py                 # FastAPI 入口 + lifespan
│   ├── config.py               # 配置中心（.env + 数据库双来源）
│   ├── database.py             # 数据库连接 + 模型注册 + init_db()
│   ├── redis_client.py         # Redis 缓存客户端
│   ├── deps.py                 # 依赖注入(JWT)
│   ├── schemas.py              # Pydantic 模型
│   ├── dialogue_engine.py      # 对话引擎
│   ├── rag_engine.py           # RAG 引擎（MiniMax + 关键词降级）
│   ├── routers/                # 10 个 API 路由模块
│   │   ├── auth.py             # 认证（注册/登录/验证码）
│   │   ├── dialogue.py         # 时空对话
│   │   ├── exploration.py      # 探索记录
│   │   ├── vote.py             # 投票系统
│   │   ├── rating.py           # 评分系统
│   │   ├── champion.py         # 冠军卡牌
│   │   ├── signature.py        # 签名上传
│   │   ├── events.py           # 历史事件 API
│   │   ├── rag.py              # RAG 知识库 API
│   │   └── config.py           # 系统配置管理
│   ├── models/                 # 9 个 ORM 模型
│   │   ├── user.py             # users 表
│   │   ├── dialogue.py         # dialogue_sessions 表
│   │   ├── exploration_record.py # exploration_records 表
│   │   ├── vote.py             # votes 表
│   │   ├── rating.py           # ratings 表
│   │   ├── champion_card.py    # champion_cards 表
│   │   ├── signature.py        # signatures 表
│   │   ├── event.py            # history_events 表
│   │   └── system_config.py    # system_config 表
│   ├── data/                   # 初始化种子数据
│   │   ├── __init__.py
│   │   ├── config_data.py      # 35 项默认系统配置
│   │   └── events_data.py      # 50 个历史事件数据
│   └── requirements.txt        # Python 依赖
├── deploy/
│   ├── nginx.conf              # 开发环境 Nginx 配置
│   └── nginx.prod.conf         # 生产环境 Nginx 配置
├── docker-compose.yml          # Docker 部署配置
├── .env.example                # 环境变量示例
├── start.ps1                   # Windows 一键启动脚本
├── stop.ps1                    # Windows 一键停止脚本
└── docs/
    ├── FEATURES.md             # 本文档
    ├── MIGRATION.md            # 跨平台迁移指南
    └── specs/                  # 设计规格文档
```

---

## 八、开发进度总览

| 模块 | 前端 | 后端 | 状态 | 备注 |
|------|------|------|------|------|
| 认证系统 | ✅ | ✅ | 完成 | 邮箱验证码+JWT |
| 宇宙星图首页 | ✅ | - | 完成 | Canvas+SVG+DOM |
| 事件详情+星链 | ✅ | - | 完成 | 行星可视化+传送动画 |
| 时空对话 | ✅ | ✅ | 完成 | 预置剧本+多轮对话 |
| 探索记录 | ✅ | ✅ | 完成 | 计时+统计 |
| 投票系统 | ✅ | ✅ | 完成 | 赞同/反对/收藏 |
| 评分系统 | ✅ | ✅ | 完成 | 5星+文字评价 |
| 冠军卡牌 | ✅ | ✅ | 完成 | 稀有度+排行 |
| 个人中心 | ✅ | - | 完成 | 三Tab整合 |
| 排行榜 | ✅ | - | 完成 | 时间段排行 |
| 签名上传 | ✅ | ✅ | 完成 | 拖拽上传 |
| 邮件服务 | - | ✅ | 完成 | SMTP配置 |
| 历史事件 API | ✅ | ✅ | 完成 | 50 个事件+筛选+搜索 |
| RAG 知识库 | - | ✅ | 完成 | MiniMax 向量搜索+问答 |
| 系统配置管理 | - | ✅ | 完成 | 数据库配置+热加载 |
| 数据库自动初始化 | - | ✅ | 完成 | 自动建表+种子数据 |
| 后台管理系统 | ❌ | ❌ | 待开发 | 文献上传+RAG |
| 每日爬虫任务 | ❌ | ❌ | 待开发 | 历史数据采集 |

---

## 九、待开发功能 (Future)

### 9.1 后台管理系统
- 历史文献上传
- 事件管理（CRUD）
- 用户管理
- 数据统计面板

### 9.2 每日爬虫任务
- 定定爬取历史数据
- 事件去重处理
- 自动生成事件文档

---

## 十、更新日志

### 2026-06-01

**Bug Fix**:
- 修复数据库启动时未自动建表的问题：`database.py` 中 `Base.metadata` 在 `create_all` 前未注册任何模型，通过添加 `from . import models` 解决
- 修复 `events_data.py` 中文引号导致 Python 语法错误的问题

**New Features**:
- 新增 `backend/data/` 目录：`config_data.py`（35 项默认配置）+ `events_data.py`（50 个历史事件）
- 新增 `backend/routers/events.py`：历史事件 CRUD API（列表/搜索/详情）
- 新增 `backend/routers/rag.py`：RAG 知识库 API（搜索/问答/索引重建）
- 新增 `backend/routers/config.py`：系统配置管理 API（查询/更新）
- 新增 `backend/rag_engine.py`：RAG 引擎（MiniMax 向量嵌入 + 关键词降级）
- 新增 `backend/models/event.py`：`history_events` 数据表
- 新增 `backend/models/system_config.py`：`system_config` 数据表
- 数据库表从 7 张扩展到 9 张
- 数据库启动时自动 seed 35 项配置和 50 个历史事件
- 更新 `.env.example`：添加 `MINIMAX_API_KEY` 配置项
- 更新 `docker-compose.yml`：完整的 MySQL + Redis + Backend + Frontend + Nginx 部署配置

**Documentation**:
- 更新 FEATURES.md：添加事件 API、RAG、配置管理等模块文档
- 添加数据库自动初始化说明
- 添加部署配置清单
- 添加数据库选择策略说明
