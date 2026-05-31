# 历史星链探索 - 后端服务

赛博朋克风格的历史探索游戏后端 API，基于 Python FastAPI 构建。

## 技术栈

- **Web框架**: FastAPI
- **数据库**: MySQL 8.0+ (异步驱动 aiomysql)
- **缓存**: Redis
- **ORM**: SQLAlchemy 2.0 (async)
- **数据校验**: Pydantic v2

## 服务器信息

- **服务器IP**: 111.231.50.67
- **API端口**: 8000
- **MySQL**: 111.231.50.67:3306
- **Redis**: 111.231.50.67:6379

## 目录结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置文件
├── database.py             # 数据库连接配置
├── redis_client.py         # Redis 客户端配置
├── schemas.py              # Pydantic 模型定义
├── requirements.txt        # Python 依赖
├── models/                 # SQLAlchemy 模型
│   ├── __init__.py
│   ├── exploration_record.py   # 探索记录模型
│   ├── rating.py               # 评分模型
│   ├── vote.py                 # 投票模型
│   ├── signature.py            # 签名模型
│   └── champion_card.py        # 冠军卡片模型
└── routers/                # API 路由
    ├── __init__.py
    ├── exploration.py      # 探索记录 API
    ├── rating.py           # 评分 API
    ├── vote.py             # 投票 API
    ├── signature.py        # 签名上传 API
    └── champion.py         # 冠军卡片 API
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 创建数据库

```sql
CREATE DATABASE IF NOT EXISTS historical_starlink
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
```

### 3. 配置环境变量（可选）

```bash
# MySQL
set MYSQL_HOST=111.231.50.67
set MYSQL_PORT=3306
set MYSQL_USER=root
set MYSQL_PASSWORD=your_password
set MYSQL_DATABASE=historical_starlink

# Redis
set REDIS_HOST=111.231.50.67
set REDIS_PORT=6379
set REDIS_DB=0
```

### 4. 启动服务

```bash
# 开发模式（自动热重载）
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用 python 直接运行
python -m backend.main
```

### 5. 访问文档

- Swagger UI: http://111.231.50.67:8000/docs
- ReDoc: http://111.231.50.67:8000/redoc
- 健康检查: http://111.231.50.67:8000/health

## API 接口一览

### 探索记录 `/api/exploration`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/exploration/records | 创建探索记录 |
| GET | /api/exploration/records | 查询探索记录列表 |
| GET | /api/exploration/records/{id} | 获取单条记录 |
| GET | /api/exploration/stats | 探索统计信息 |
| DELETE | /api/exploration/records/{id} | 删除探索记录 |

### 评分 `/api/rating`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/rating | 创建评分 |
| PUT | /api/rating/{id} | 更新评分 |
| GET | /api/rating | 查询评分列表 |
| GET | /api/rating/stats/{event_id} | 事件评分统计 |
| DELETE | /api/rating/{id} | 删除评分 |

### 投票 `/api/vote`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/vote | 创建/切换投票 |
| GET | /api/vote/stats/{event_id} | 事件投票统计 |
| GET | /api/vote/my | 用户投票记录 |
| GET | /api/vote/batch-stats | 批量投票统计 |

### 签名 `/api/signature`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/signature/upload | 上传签名图片 |
| GET | /api/signature | 查询签名列表 |
| GET | /api/signature/{id} | 获取单条签名 |
| DELETE | /api/signature/{id} | 删除签名 |

### 冠军卡片 `/api/champion`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/champion | 创建/更新冠军卡片 |
| GET | /api/champion | 查询冠军卡片列表 |
| GET | /api/champion/stats/{session_id} | 用户卡片统计 |
| PUT | /api/champion/{id} | 更新冠军卡片 |
| DELETE | /api/champion/{id} | 删除冠军卡片 |

## 数据库表

启动时自动创建以下表：

- `exploration_records` - 探索记录
- `ratings` - 评分
- `votes` - 投票
- `signatures` - 签名
- `champion_cards` - 冠军卡片

## 注意事项

1. 数据库表在首次启动时自动创建（通过 SQLAlchemy 的 `create_all`）
2. Redis 连接失败时服务仍可正常运行，仅缓存功能不可用
3. 签名上传文件存储在 `uploads/` 目录下，按会话ID分组
4. 所有接口返回统一 JSON 格式：`{code, message, data}`
