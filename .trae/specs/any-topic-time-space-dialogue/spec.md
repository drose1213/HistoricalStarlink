# 任意话题时空对话 Spec

## Why
当前 "开启时空对话" 功能仅支持 5 个预置剧本事件（秦统一六国 / 汉帝国 / 长城修建 / 造纸术 / 火药），用户必须从固定事件列表中选取才能进入对话。这导致：
- 用户在首页输入"AI 发展史""太空探索""量子物理"等任意话题时无法开启时空穿越
- 时空探索的入口被限制在已知剧本范围，违背"历史星链 + 时空对话"的核心体验承诺
- RAG 引擎已支持 5+ 历史事件 + 知识库 + embedding 检索，但**对话流程未利用 RAG 动态生成剧本/回复/结局**

本次需要让时空对话**完全开放**：用户输入任意话题都能进入对话流程，并由 RAG 引擎兜底生成 NPC 回应与最终结局。

## What Changes

### 后端 — dialogue_engine.py
- 新增 `start_dynamic_dialogue(topic: str, session_id: str) -> dict`：
  - 不依赖预置剧本，topic 任意字符串
  - 自动从 `HISTORY_EVENTS` + 知识库检索最相关的 1 个历史事件作为"NPC 锚点"
  - 通过 `RAG.full_rag_query(topic)` 生成开场白（带时代背景标签）
  - 写入 `DialogueSession.event_id = "dynamic_{slug}"`、`is_dynamic = true`
- 新增 `process_dynamic_choice(...)` 与 `process_dynamic_free_text(...)`：
  - 复用 `_keyword_fallback_scores` 容错 + `classify_intent` 意图分类
  - NPC 回应：优先调 `RAG.full_rag_query`，失败回退到关键词拼接的兜底文本
  - choices 仍写入 `dialogue_history`，但**不**强求预置 ending；轮次由 `MAX_ROUND_LIMIT = 10` 控制
- 新增 `_build_dynamic_ending(topic, choices_made, free_texts) -> str`：
  - 调 `RAG.full_rag_query(topic + " 总结 + 影响")` 生成 1 段总结性结局
  - 截断 280 字
- 新增 `event_id` 解析兼容：接受 `dynamic_*` 前缀，与 `qin_unification` 等预置事件路由并行

### 后端 — routers/dialogue.py
- 新增 `POST /api/dialogue/dynamic/start`：body `{ topic, session_id? }`，返回 `{ dialogue_id, event_id: "dynamic_*", opening, is_dynamic: true }`
- 新增 `POST /api/dialogue/dynamic/{dialogue_id}/choice` / `.../chat`：与现有预置事件共用 `DialogueSession` 表 + `is_dynamic` 标记区分
- `start` 路由：增加 fallback — 如果 `event_id` 形如 `dynamic:*` 则调 `start_dynamic_dialogue` 分支

### 数据库
- `DialogueSession.is_dynamic : Boolean = False`（兼容老数据，默认 False）
- 不需新增表，复用 `DialogueSession + DialogueMessage + UserExplorationProfile`

### 前端 — HomeView / 首页输入
- 首页中央"穿越"按钮：保留预置事件入口（"重新开始"按钮）
- 输入框 placeholder 改为 "输入任意话题开启时空对话..."，输入任意文本后直接 POST `/api/dialogue/dynamic/start`
- 成功后跳转到 `DialogueView`，eventId 形如 `dynamic_*`，DialogueView 兼容 dynamic 与预置两种剧本

### RAG 兜底
- 复用 `RAG.full_rag_query(query, top_k=3)` 链路（之前已修过索引懒构建 + dict 容错）
- 若 embedding API 不可用（`MINIMAX_API_KEY=""`），回退到 `_keyword_search` 拼装文本
- `_ensure_seed_index` 已存在，dynamic 模式不依赖 `build_index` 异步流程

## Impact
- Affected specs:
  - `time-space-dialogue-enhance`（既有预置剧本能力，保持兼容不破坏）
  - `dialogue-branch-endings-and-profile`（profile / branches 接口可继续用于 dynamic 事件，`available_endings` 会少但接口契约不变）
- Affected code:
  - `backend/dialogue_engine.py`（新增 ~80 行）
  - `backend/routers/dialogue.py`（新增 1 个 router + 3 个 endpoint）
  - `backend/models/dialogue.py`（`DialogueSession` 加 `is_dynamic` 字段）
  - `backend/database.py`（新增字段 ALTER TABLE 兼容老库）
  - `frontend/src/views/HomeView.vue` / `DialogueView.vue`（入口 + 路由）
  - `frontend/src/stores/dialogue.ts`（`startDialogue` 接受 dynamic 模式）

## ADDED Requirements

### Requirement: 任意话题开启时空对话
The system SHALL allow users to start a time-space dialogue with **any free-text topic**, not limited to the 5 preset events.

#### Scenario: 首页输入任意话题开启对话
- **WHEN** 用户在首页输入框输入任意文本（如"AI 发展史" / "唐朝" / "太空探索"）并点击"开启时空对话"
- **THEN** 后端创建 `DialogueSession(is_dynamic=True, event_id="dynamic_<slug>")`，返回开场白
- **AND** 前端跳转至 `DialogueView`，`eventId` 为 `dynamic_*` 形式

#### Scenario: 预置事件入口仍可用
- **WHEN** 用户点击首页"重新开始"按钮或预置事件卡片
- **THEN** 仍走原 `POST /api/dialogue/start` 流程，行为不变

### Requirement: RAG 动态生成 NPC 回应
The system SHALL generate NPC responses for dynamic dialogues by calling `RAG.full_rag_query`, falling back to keyword search if RAG is unavailable.

#### Scenario: dynamic 模式生成 choice 回应
- **WHEN** dynamic 对话收到 `process_dynamic_choice`
- **THEN** 后端调 `RAG.full_rag_query(topic + choice.mood)`，截断 500 字
- **AND** 若 embedding API 返回空，回退到 `_keyword_search` 拼装文本
- **AND** choices 累计写入 `dialogue_history`

#### Scenario: dynamic 模式生成 free_text 回应
- **WHEN** 用户在 dynamic 对话中发送自由文本
- **THEN** 调 `RAG.full_rag_query(topic + free_text)`，同样截断 500 字
- **AND** 不抛异常（即使 RAG 完全失败，至少返回"时空之门暂时无法回应"）

### Requirement: RAG 动态生成结局
The system SHALL generate a final ending for dynamic dialogues via RAG, not requiring a preset `endings` dict.

#### Scenario: dynamic 对话到达第 10 轮 / 用户主动结束
- **WHEN** dynamic 对话满足结束条件（MAX_ROUND_LIMIT / is_completed）
- **THEN** 调 `_build_dynamic_ending(topic, choices_made, free_texts)`，返回 1 段 ≤ 280 字的总结性结局
- **AND** `ending_type = "rag_dynamic"`
- **AND** `UserExplorationProfile` 仍记录（`ending_type="rag_dynamic"`）

### Requirement: dynamic 模式路径签名
The system SHALL compute `path_signature` (A-T-D style) for dynamic dialogues just like preset events, so user exploration profile works uniformly.

#### Scenario: dynamic 对话累计 4 维画像
- **WHEN** dynamic 对话每轮 choice / free_text 完成
- **THEN** 响应中追加 `cumulative_impact` 字段（4 维分数 0-100）

## MODIFIED Requirements

### Requirement: 既有预置事件行为保持兼容
- `qin_unification` / `han_empire` / `great_wall_construction` / `invention_of_paper` / `invention_of_gunpowder` 5 个预置事件的所有接口、测试、剧本完全不变
- `is_dynamic = False` 是默认值

## REMOVED Requirements
- 无
