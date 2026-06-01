# 历史星链探索 · Historical Starlink Explorer

> 一个以赛博朋克 + 宇宙星图为视觉语言的历史文化探索平台 —— 把 50 个中外历史事件织成一张可视化的「星链关系网」，支持时空对话、投票、评分、卡牌、排行榜等互动玩法。

[![Vue 3](https://img.shields.io/badge/Vue-3.x-42b883?logo=vue.js)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)

---

## ✨ 项目亮点

- 🌌 **宇宙星图首页**：Canvas 星空 + SVG 星座连线，50 个历史事件作为可点击的星节点
- 🔗 **事件星链**：每个事件展示「历史原因」与「历史影响」关联事件，支持飞船传送动画跳转
- 💬 **时空对话**：每个事件有独立 NPC 角色，支持剧本选择 + 自由文本多轮对话 + 分支结局
- 🗳 **互动玩法**：投票（赞同/反对/收藏）、5 星评分、卡牌解锁、排行榜
- 🤖 **RAG 智能问答**：基于 MiniMax API 的向量语义检索，无 Key 时自动降级为关键词匹配
- 🗂 **数据库自初始化**：首次启动自动建表 + 自动 seed 35 项配置 + 50 个历史事件
- 🐳 **一键 Docker 部署**：MySQL + Redis + Backend + Frontend + Nginx 全栈编排

---

## 🛠 技术栈

### 前端
| 技术 | 用途 |
|------|------|
| Vue 3 (Composition API) | 视图层 |
| TypeScript | 类型系统 |
| Pinia | 状态管理 |
| Vue Router | 路由（Hash 模式） |
| Vite | 构建工具 |
| 原生 Canvas + SVG | 宇宙星图渲染 |

### 后端
| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架 |
| SQLAlchemy | ORM |
| Pydantic | 数据校验 |
| PyMySQL / sqlite3 | 数据库驱动 |
| redis-py | 缓存（可选） |
| python-jose | JWT 鉴权 |
| MiniMax API | RAG 向量嵌入 + AI 问答 |

### 基础设施
| 技术 | 用途 |
|------|------|
| MySQL 8.0 | 主数据库 |
| SQLite | 自动回退数据库（无 MySQL 时） |
| Redis 7 | 缓存 / 会话 |
| Nginx | 反向代理 |
| Docker Compose | 一键编排 |

---

## 🚀 快速开始

### 方式一：本地开发（Windows 一键脚本）

```powershell
# 1. 克隆项目
git clone https://github.com/drose1213/HistoricalStarlink.git
cd HistoricalStarlink

# 2. 复制环境变量
Copy-Item .env.example .env
# 用编辑器修改 .env 中的 MYSQL_PASSWORD / JWT_SECRET_KEY / SMTP_PASSWORD / MINIMAX_API_KEY

# 3. 一键启动（自动启动后端 + 前端）
.\start.ps1

# 4. 访问应用
#    前端: http://localhost:3000
#    后端: http://localhost:8000
#    API 文档: http://localhost:8000/docs
```

### 方式二：本地手动启动

```powershell
# 后端
python -m venv venv
.\venv\Scripts\pip install -r backend\requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 前端（新开一个终端）
cd frontend
npm install
npm run dev
```

### 方式三：Docker Compose 一键部署（生产推荐）

```bash
# 1. 准备 .env
cp .env.example .env
# 修改 MYSQL_PASSWORD / JWT_SECRET_KEY

# 2. 启动所有服务
docker-compose up -d

# 3. 查看状态
docker-compose ps

# 4. 访问
#    应用:    http://localhost
#    API 文档: http://localhost:8000/docs
```

Docker Compose 会自动启动：
- `mysql:8.0` (端口 3306)
- `redis:7-alpine` (端口 6379)
- `backend` (FastAPI，端口 8000)
- `frontend` (Vue 3 静态资源)
- `nginx:alpine` (反向代理，端口 80)

---

## ⚙️ 环境变量

完整配置参考 [.env.example](.env.example)：

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `DB_DRIVER` | 否 | `auto` | `auto` / `mysql` / `sqlite` |
| `MYSQL_HOST` | ✅ | `127.0.0.1` | MySQL 主机 |
| `MYSQL_PORT` | 否 | `3306` | MySQL 端口 |
| `MYSQL_USER` | ✅ | `root` | MySQL 用户名 |
| `MYSQL_PASSWORD` | ✅ | - | MySQL 密码 |
| `MYSQL_DATABASE` | 否 | `historical_starlink` | 数据库名 |
| `REDIS_HOST` | 否 | `127.0.0.1` | Redis 主机（不配则禁用缓存） |
| `REDIS_PORT` | 否 | `6379` | Redis 端口 |
| `JWT_SECRET_KEY` | ✅ | - | JWT 签名密钥（生产必改） |
| `SMTP_USER` | 否 | - | 邮箱（QQ 邮箱） |
| `SMTP_PASSWORD` | 否 | - | SMTP 授权码（非登录密码） |
| `MINIMAX_API_KEY` | 否 | - | MiniMax API Key（不配则 RAG 降级） |
| `SERVER_PORT` | 否 | `8000` | 后端端口 |
| `FRONTEND_PORT` | 否 | `3000` | 前端开发端口 |

### 数据库选择策略

| `DB_DRIVER` | 行为 | 适用场景 |
|---|---|---|
| `auto`（默认） | TCP 探测 MySQL：连上用 MySQL，连不上自动降级 SQLite | 开发 / 测试 |
| `mysql` | 强制使用 MySQL | **生产环境推荐** |
| `sqlite` | 强制使用 SQLite | 本地开发 |

> ⚠️ **生产环境务必设置 `DB_DRIVER=mysql`**，避免 MySQL 临时不可用时静默降级到 SQLite 导致数据隔离。

---

## 📦 项目结构

```
HistoricalStarlink/
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 页面级组件
│   │   ├── components/         # 可复用组件
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── api/                # API 请求封装
│   │   ├── router/             # 路由配置
│   │   ├── types/              # TypeScript 类型
│   │   └── data/               # 共享事件数据
│   └── package.json
├── backend/                    # FastAPI 后端
│   ├── routers/                # 10 个 API 路由模块
│   ├── models/                 # 9 个 ORM 模型
│   ├── data/                   # 初始化种子数据
│   │   ├── config_data.py      # 35 项默认配置
│   │   └── events_data.py      # 50 个历史事件
│   ├── main.py                 # FastAPI 入口 + lifespan
│   ├── config.py               # 配置中心
│   ├── database.py             # 数据库 + 模型注册
│   └── requirements.txt
├── deploy/                     # Nginx 配置
│   ├── nginx.conf              # 开发环境
│   └── nginx.prod.conf         # 生产环境
├── docs/
│   ├── FEATURES.md             # 功能模块全景图
│   ├── MIGRATION.md            # 跨平台迁移指南
│   └── specs/                  # 设计规格文档
├── docker-compose.yml          # Docker 编排
├── .env.example                # 环境变量模板
├── start.ps1                   # Windows 启动脚本
├── stop.ps1                    # Windows 停止脚本
└── README.md                   # 本文件
```

---

## 🎯 核心功能

| 模块 | 描述 |
|------|------|
| 🔐 认证系统 | 邮箱验证码 + JWT（7 天） + 赛博朋克邮件模板 |
| 🌌 宇宙星图 | Canvas 星空 + SVG 星座 + 50 事件星节点 |
| 🔗 事件星链 | 行星可视化 + 因果关系网 + 飞船传送动画 |
| 💬 时空对话 | 预置剧本 + 多轮对话 + 分支结局 + 打字动画 |
| 🗺 探索记录 | 计时 + 统计 + 历史列表 |
| 🗳 投票系统 | 赞同/反对/收藏 + 热门排行 |
| ⭐ 评分系统 | 5 星 + 文字评价 |
| 🃏 冠军卡牌 | 4 稀有度 + 全服排行 |
| 👤 个人中心 | 探索/趋势/卡牌三 Tab |
| 🏆 排行榜 | 日/周/月/年 + 领奖台 |
| ✍️ 签名上传 | 拖拽上传 + 列表管理 |
| 🤖 RAG 知识库 | MiniMax 向量检索 + 关键词降级 |
| ⚙️ 系统配置 | 数据库存储 + 热加载 |

👉 详细功能说明见 [docs/FEATURES.md](docs/FEATURES.md)

---

## 📡 主要 API 端点

| 模块 | 端点 |
|------|------|
| 认证 | `POST /api/auth/send-code` · `POST /api/auth/register` · `POST /api/auth/login` |
| 事件 | `GET /api/events` · `GET /api/events/{id}` · `GET /api/events/search?q=xxx` |
| 对话 | `POST /api/dialogue/start` · `POST /api/dialogue/choice` · `POST /api/dialogue/chat` |
| 探索 | `POST /api/exploration/start` · `POST /api/exploration/end` · `GET /api/exploration/records` |
| 投票 | `POST /api/vote` · `GET /api/vote/stats/{event_id}` |
| 评分 | `POST /api/rating` · `GET /api/rating/stats/{event_id}` |
| 卡牌 | `GET /api/champion` · `GET /api/champion/stats/{session_id}` |
| RAG | `POST /api/rag/search` · `POST /api/rag/ask` · `POST /api/rag/rebuild` |
| 配置 | `GET /api/config` · `GET /api/config/{key}` · `PUT /api/config/{key}` |
| 健康检查 | `GET /health` · `GET /docs` (Swagger) |

---

## 🗄 数据库自动初始化

应用首次启动时（FastAPI lifespan）会自动执行：

```
lifespan.start
  ├─ init_db()              → 创建所有表（Base.metadata.create_all）
  ├─ _seed_configs()        → 写入 35 项默认系统配置
  ├─ load_db_config_safe()  → 从数据库加载配置到运行时
  └─ _seed_events()         → 写入 50 个历史事件
```

数据库表清单（9 张）：

- `users` · `dialogue_sessions` · `exploration_records`
- `votes` · `ratings` · `champion_cards` · `signatures`
- `history_events` · `system_config`

---

## 🧪 50 个历史事件概览

**中国历史（26 个）**：长城修建、造纸术、火药、指南针、印刷术、商鞅变法、秦统一六国、汉朝建立、丝绸之路、唐朝盛世、安史之乱、宋朝科技、蒙古帝国、郑和下西洋、鸦片战争、太平天国、洋务运动、戊戌变法、辛亥革命、五四运动、长征、新中国成立、改革开放…

**世界历史（19+ 个）**：亚历山大东征、罗马帝国、十字军东征、黑死病、文艺复兴、宗教改革、光荣革命、启蒙运动、美国独立、法国大革命、工业革命、一战、二战、冷战、柏林墙倒塌、互联网诞生、人类登月…

---

## 🔧 常用脚本

```powershell
# 启动
.\start.ps1

# 停止
.\stop.ps1

# 查看运行状态
.\status.ps1

# Docker 部署
docker-compose up -d          # 启动
docker-compose down           # 停止
docker-compose logs -f backend # 查看后端日志
```

---

## 📚 文档导航

- 📖 [功能模块全景图 (FEATURES.md)](docs/FEATURES.md) — 14 个功能模块详解
- 🔄 [跨平台迁移指南 (MIGRATION.md)](docs/MIGRATION.md) — 本地 ↔ 服务器迁移
- 📐 [设计规格文档 (specs/)](docs/specs/) — 首页 / 星图设计稿

---

## 🛣 Roadmap

- [ ] 后台管理系统（文献上传 / 事件 CRUD / 用户管理）
- [ ] 每日爬虫任务（历史数据自动采集）
- [ ] 移动端 PWA 适配
- [ ] i18n 国际化（中英双语）
- [ ] WebSocket 实时通知

---

## 📄 License

MIT License — 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- 50 个历史事件数据由项目作者整理编写
- 视觉设计灵感来源于「赛博朋克 2077」与「文明」系列游戏
- 部署运维借助 Docker / Nginx / MySQL 社区

---

<p align="center">
  <sub>Built with ❤️ by Historical Starlink Team</sub>
</p>
