# 文明星链：遗迹探索 — 功能模块全景图

> **技术栈**: Vue 3 + TypeScript + Pinia + FastAPI + SQLAlchemy + MySQL/SQLite + Redis  
> **服务器**: `111.231.50.67`  
> **最后更新**: 2026-05-30

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
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ │
│     └────────┴────────┴────────┴────────┴────────┘     │
│              SQLAlchemy ORM + Redis Cache                  │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │ MySQL (优先)          │
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
- 5个历史事件星节点（可点击跳转详情）
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
  related: {
    causes: Array<{ id: string; weight: number }>
    consequences: Array<{ id: string; weight: number }>
  }
}
```

#### 当前 7 个事件
商鞅变法(-356) → 秦始皇统一六国(-221) → 大汉帝国建立(-202)  
亚历山大东征(-334) → 罗马帝国建立(-27)  
法国大革命(1789) → 工业革命(1760)

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

#### NPC 角色映射
| 事件 | NPC | 角色 |
|------|-----|------|
| 商鞅变法 | 商鞅 | 变法主导者 |
| 秦始皇统一六国 | 秦始皇 | 皇帝 |
| 大汉帝国建立 | 刘邦 | 开国皇帝 |
| 亚历山大东征 | 亚历山大 | 军事天才 |
| 罗马帝国建立 | 屋大维 | 奥古斯都 |
| 法国大革命 | 巴黎市民 | 革命参与者 |
| 工业革命 | 瓦特 | 发明家 |

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

#### 稀有度系统
| 稀有度 | 边框颜色 | 特效 |
|--------|---------|------|
| 传说 (legendary) | 金色 | 金色闪光动画 |
| 史诗 (epic) | 紫色 | 紫色光晕 |
| 稀有 (rare) | 青色 | 青色发光 |
| 普通 (common) | 灰色 | 无特效 |

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
- 前三名领奖台（🥇🥈🥉）
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

## 四、共享数据

### 事件数据 (`src/data/events.ts`)

统一管理所有历史事件数据，供多个页面引用：
- HomeView（宇宙星图）
- EventDetailView（详情+星链）
- ProfileView（探索记录+趋势）
- CosmicMap（星图可视化）
- LeaderboardView（排行榜）

#### 导出函数
```typescript
allEvents: HistoryEvent[]           // 所有事件
getEventById(id): HistoryEvent      // 按ID获取
getRelatedEvents(id, type): ...     // 获取关联事件
searchEvents(keyword): HistoryEvent[] // 关键词搜索
```

---

## 五、CSS 变量系统

所有组件使用统一的 CSS 变量：

```css
--cyan-core: #31f7ff        /* 青色主色 */
--pink-core: #ff35f3        /* 粉色强调 */
--accent-gold: #d4a84b      /* 金色/历史 */
--bg-primary: #05070d       /* 深空黑背景 */
--bg-card: #0f1a2d          /* 卡片背景 */
--bg-input: #0a1525         /* 输入框背景 */
--border-cyan: rgba(49,247,255,0.2)
--border-pink: rgba(255,53,243,0.2)
--border-subtle: rgba(255,255,255,0.08)
--text-light: #e0e6f0
--text-muted: #5a6478
--font-serif: 'Noto Serif SC', serif
--font-mono: 'JetBrains Mono', monospace
--font-display: 'Orbitron', sans-serif
```

---

## 六、后端数据库表

| 表名 | 模型文件 | 说明 |
|------|---------|------|
| `users` | `models/user.py` | 用户表（JWT鉴权） |
| `dialogue_sessions` | `models/dialogue.py` | 对话会话 |
| `exploration_records` | `models/exploration_record.py` | 探索记录 |
| `votes` | `models/vote.py` | 投票记录 |
| `ratings` | `models/rating.py` | 评分记录 |
| `champion_cards` | `models/champion_card.py` | 冠军卡牌 |
| `signatures` | `models/signature.py` | 签名图片 |

---

## 七、开发进度总览

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
| 后台管理系统 | ❌ | ❌ | 待开发 | 文献上传+RAG |
| 每日爬虫任务 | ❌ | ❌ | 待开发 | 历史数据采集 |
| RAG知识库 | ❌ | ❌ | 待开发 | 向量搜索+实时API |

---

## 八、待开发功能 (Future)

### 8.1 后台管理系统
- 历史文献上传
- 事件管理（CRUD）
- 用户管理
- 数据统计面板

### 8.2 每日爬虫任务
- 定时爬取历史数据
- 事件去重处理
- 自动生成事件文档

### 8.3 RAG 知识库
- 文档向量化存储
- 用户搜索匹配
- 实时 API 查询
- 知识库更新机制

---

## 九、开发环境配置

### 前端
```bash
cd frontend
npm install
npm run dev        # 开发服务器 http://localhost:5173
npm run build      # 生产构建
```

### 后端
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload  # 开发服务器 http://localhost:8000
```

### 环境变量 (.env)
```env
# 数据库
DB_DRIVER=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=xxx
MYSQL_DATABASE=historical_starlink

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=xxx

# 邮件
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=xxx@qq.com
SMTP_PASSWORD=xxx
SMTP_FROM=xxx@qq.com

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 十、文件结构索引

```
HistoricalStarlink/
├── frontend/
│   └── src/
│       ├── views/              # 8个页面组件
│       │   ├── HomeView.vue           # 首页
│       │   ├── EventDetailView.vue    # 事件详情
│       │   ├── ProfileView.vue        # 个人中心
│       │   ├── ChampionsView.vue      # 卡牌展馆
│       │   ├── LeaderboardView.vue    # 排行榜
│       │   ├── ExploreView.vue        # 探索记录(旧)
│       │   ├── TrendsView.vue         # 趋势分析(旧)
│       │   └── AuthView.vue           # 登录/注册
│       ├── components/         # 8个可复用组件
│       │   ├── CosmicMap.vue          # 宇宙星图
│       │   ├── StarlinkPlanets.vue    # 星链行星
│       │   ├── DialogueExplorer.vue   # 时空对话
│       │   ├── ExplorationRecord.vue  # 探索记录
│       │   ├── VotingSystem.vue       # 投票系统
│       │   ├── RatingSystem.vue       # 评分系统
│       │   ├── ChampionCard.vue       # 卡牌展示
│       │   └── SignatureUpload.vue    # 签名上传
│       ├── stores/             # 8个Pinia Store
│       │   ├── auth.ts, app.ts, dialogue.ts
│       │   ├── exploration.ts, vote.ts, rating.ts
│       │   ├── champion.ts, signature.ts
│       ├── api/                # 8个API模块
│       │   ├── request.ts, auth.ts, dialogue.ts
│       │   ├── exploration.ts, vote.ts, rating.ts
│       │   ├── champion.ts, signature.ts
│       ├── data/
│       │   └── events.ts       # 共享事件数据
│       ├── utils/
│       │   ├── auth.ts         # requireAuth()
│       │   └── session.ts      # sessionId生成
│       ├── types/
│       │   └── index.ts        # TypeScript类型定义
│       └── router/
│           └── index.ts        # 路由配置
├── backend/
│   ├── main.py                 # FastAPI入口
│   ├── config.py               # 配置中心
│   ├── database.py             # 数据库连接
│   ├── redis_client.py         # Redis缓存
│   ├── deps.py                 # 依赖注入(JWT)
│   ├── schemas.py              # Pydantic模型
│   ├── dialogue_engine.py      # 对话引擎
│   ├── routers/                # 7个API路由
│   │   ├── auth.py, dialogue.py, exploration.py
│   │   ├── vote.py, rating.py, champion.py, signature.py
│   └── models/                 # 7个数据库模型
│       ├── user.py, dialogue.py, exploration_record.py
│       ├── vote.py, rating.py, champion_card.py, signature.py
└── docs/
    └── FEATURES.md             # 本文档
```
