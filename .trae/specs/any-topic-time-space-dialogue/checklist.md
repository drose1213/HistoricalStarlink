# 任意话题时空对话 — 验收清单

## 后端 — 模型层
- [x] `DialogueSession` 增加 `is_dynamic : Boolean = False` 字段
- [x] `to_dict()` 方法追加 `is_dynamic` 字段
- [x] 数据库迁移脚本可处理老库（ALTER TABLE）
- [x] 启动后端无 SQLAlchemy 警告 / 错误

## 后端 — 引擎层
- [x] `start_dynamic_dialogue(topic, session_id)` 创建会话并生成开场白
- [x] `process_dynamic_choice` 走 RAG → 关键词 fallback
- [x] `process_dynamic_free_text` 走 RAG → 关键词 fallback
- [x] `_build_dynamic_ending` 截断 280 字
- [x] RAG 全部失败时返回 `"时空之门暂时无法回应..."` 而非抛 500
- [x] 路径签名 + 4 维画像对 dynamic 模式生效
- [x] `MAX_DYNAMIC_ROUNDS = 10` 同样适用于 dynamic

## 后端 — 路由层
- [x] `POST /api/dialogue/dynamic/start` 接收任意 topic 返回 200
- [x] `POST /api/dialogue/dynamic/{id}/choice` / `/chat` / `/end` 复用现有错误码 (400/404/410)
- [x] 显式 `db.commit()` + 异常 `db.rollback()`
- [x] 老 endpoint `POST /api/dialogue/start` 预置事件行为不变（qin/han 等 5 个事件仍可正常开启）

## 前端 — 首页入口
- [x] 首页输入框 placeholder 改为"输入任意话题开启时空对话..."
- [x] 提交时正确路由到 `/api/dialogue/dynamic/start`
- [x] 预置事件入口（"重新开始"按钮 / 抽屉 / 搜索）走 `/api/dialogue/start` 不变

## 前端 — DialogueView
- [x] `eventId` 形如 `dynamic_*` 时走 dynamic 接口
- [x] 4 维画像 / 路径签名展示对 dynamic 一致
- [x] 结局展示对 `rag_dynamic` 类型友好

## 测试
- [x] 11 个 dynamic 单元测试 PASS（mock RAG）
- [x] 5 个 dynamic e2e 测试 PASS
- [x] 回归保护：5 个预置事件 e2e 全部仍 PASS
- [x] 全套 `pytest backend/tests/` 137/137 PASS, 0 失败

## 端到端
- [x] e2e 验证任意 topic (中英文) → 完整 3 轮对话 → 看到 RAG 生成的 `rag_dynamic` 结局
- [x] e2e 验证非历史话题 (e.g. "test topic") 不抛 500
- [x] 关闭 RAG API (`MINIMAX_API_KEY=""`) 模拟不可用 → dynamic 对话仍能完成 (fallback → keyword → default)
- [x] `npx vue-tsc --noEmit` 无 TS / lint 错误
