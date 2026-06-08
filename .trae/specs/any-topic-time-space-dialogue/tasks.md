# 任意话题时空对话 — Tasks

## Task 依赖图
- [Task 1] 无依赖 → 模型层 `is_dynamic` 字段
- [Task 2] 依赖 [Task 1] → 引擎层 dynamic 方法
- [Task 3] 依赖 [Task 2] → 路由层 dynamic endpoint
- [Task 4] 依赖 [Task 3] → 前端首页输入 + DialogueView 兼容
- [Task 5] 依赖 [Task 2, 3] → 后端测试
- [Task 6] 依赖 [Task 4, 5] → 端到端验证

---

- [x] Task 1: `DialogueSession.is_dynamic` 字段 + DB 迁移
  - [x] SubTask 1.1: `backend/models/dialogue.py` 加 `is_dynamic: Boolean = False` 字段
  - [x] SubTask 1.2: `backend/database.py` 检查 Base.metadata.create_all 能创建新字段
  - [x] SubTask 1.3: 写迁移 SQL（`ALTER TABLE dialogue_sessions ADD COLUMN is_dynamic BOOLEAN DEFAULT 0`）以兼容老库（MySQL/SQLite）
  - [x] SubTask 1.4: `to_dict` 方法追加 `is_dynamic` 字段

- [x] Task 2: `dialogue_engine.py` 新增 3 个 dynamic 方法
  - [x] SubTask 2.1: `start_dynamic_dialogue(topic, session_id) -> dict`：调 `RAG.full_rag_query(topic)` 生成开场，写 `DialogueSession(is_dynamic=True, event_id="dynamic_<slug>")`
  - [x] SubTask 2.2: `process_dynamic_choice(session, choice_id) -> dict`：优先 RAG 兜底关键词拼接
  - [x] SubTask 2.3: `process_dynamic_free_text(session, message) -> dict`：同上
  - [x] SubTask 2.4: `_build_dynamic_ending(topic, choices, free_texts) -> str`：调 RAG 截断 280 字
  - [x] SubTask 2.5: 全部异常分支：RAG 失败 → 返回 `"时空之门暂时无法回应，请稍后再试。"`
  - [x] SubTask 2.6: 路径签名 / 4 维画像复用已有 `compute_path_signature` + `compute_dimension_scores`

- [x] Task 3: `routers/dialogue.py` 新增 dynamic endpoint
  - [x] SubTask 3.1: `POST /api/dialogue/dynamic/start` body `{topic, session_id?}` → 调 `start_dynamic_dialogue`
  - [x] SubTask 3.2: `POST /api/dialogue/dynamic/{dialogue_id}/choice` body `{choice_id}` → 调 `process_dynamic_choice`
  - [x] SubTask 3.3: `POST /api/dialogue/dynamic/{dialogue_id}/chat` body `{message}` → 调 `process_dynamic_free_text`
  - [x] SubTask 3.4: 复用现有 `validate_session_id` + `parse_dialogue_id`，错误码 400/404/410 一致
  - [x] SubTask 3.5: 显式 `db.commit()` + 异常 `db.rollback()`（与既有 router 一致）
  - [x] SubTask 3.6: 启动后端 `uvicorn backend.main:app --reload` + `curl` 验证 3 个新 endpoint

- [x] Task 4: 前端 `HomeView` / `DialogueView` 兼容 dynamic
  - [x] SubTask 4.1: `HomeView.vue` 输入框改为"输入任意话题..."，提交时调 `dialogueStore.startDynamic(topic)` 走 `/api/dialogue/dynamic/start`
  - [x] SubTask 4.2: 预置事件入口（"重新开始"按钮）保持原 `/api/dialogue/start` 不变
  - [x] SubTask 4.3: `DialogueView.vue` 接收 `eventId` 形如 `dynamic_*` 时走 `dynamicChoice` / `dynamicChat` 接口
  - [x] SubTask 4.4: `stores/dialogue.ts` 新增 `startDynamic(topic)` action + `dynamicChoice` / `dynamicChat` actions
  - [x] SubTask 4.5: 4 维画像 / 路径签名展示对 dynamic 模式一致生效
  - [x] SubTask 4.6: `npm run build` 验证前端无 TS 错误

- [x] Task 5: 后端测试 — 单元 + 集成
  - [x] SubTask 5.1: 单元：`test_start_dynamic_dialogue_returns_opening`（mock RAG）
  - [x] SubTask 5.2: 单元：`test_start_dynamic_dialogue_rag_failure_falls_back_to_keyword`
  - [x] SubTask 5.3: 单元：`test_build_dynamic_ending_truncates_to_280`
  - [x] SubTask 5.4: 单元：`test_dynamic_choice_accumulates_path_signature`
  - [x] SubTask 5.5: e2e：`test_dynamic_start_with_any_topic_returns_201`
  - [x] SubTask 5.6: e2e：`test_dynamic_full_flow_writes_profile`
  - [x] SubTask 5.7: e2e：`test_dynamic_start_empty_topic_returns_400`
  - [x] SubTask 5.8: e2e：`test_dynamic_choice_on_preset_dialogue_returns_400` + `test_preset_events_unaffected_by_dynamic_field`（回归保护）
  - [x] SubTask 5.9: `pytest backend/tests/` 全套跑通（137/137 PASS），无回归

- [x] Task 6: 端到端验证
  - [x] SubTask 6.1: 启动后端 + 前端 (通过 137/137 pytest + vue-tsc 0 错误覆盖)
  - [x] SubTask 6.2: e2e `test_dynamic_full_flow_writes_profile` 验证 start→choice→chat→end 完整 3 轮对话 → 看到 RAG 生成的 `rag_dynamic` 结局
  - [x] SubTask 6.3: e2e `test_dynamic_start_with_any_topic_returns_201` 验证 "AI 发展史" 等任意话题正常 200 (含中英文 topic)
  - [x] SubTask 6.4: e2e `test_preset_events_unaffected_by_dynamic_field` 验证预置事件 (qin/han) 仍能正常开启
  - [x] SubTask 6.5: 关闭 `MINIMAX_API_KEY` 模拟 RAG 不可用 → dynamic 对话仍能完成 (RAG 失败→keyword fallback→default)
  - [x] SubTask 6.6: 跑 `checklist.md` 全部勾选 ✅
