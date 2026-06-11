# 2026-06-10 Dynamic 对话英雄卡牌系统 - 设计文档

## 一、需求背景

当前 `dynamic` 模式下的对话（"时空对话机"）由 LLM 通过 RAG 检索 + 通用系统提示词生成回答。
存在的问题：

1. **缺乏角色身份**：用户和"时空对话机"对话时，没有具体历史人物的角色感
2. **沉浸感不足**：通用助手语气，与项目"穿越时空对话"的主题不符
3. **古风体验缺失**：用户期望与"秦始皇"对话时使用古语自称，但当前是现代语气
4. **缺乏选择权**：用户无法主动选择想与哪位历史人物对话

## 二、设计目标

为 `dynamic` 对话模式引入**英雄卡牌系统**：

- 用户输入 `topic` 后，LLM 智能推荐 1-3 个最匹配的历史人物
- 以卡牌形式展示，用户主动选择要对话的英雄
- 选定后，整个对话过程中 LLM 以该人物身份（古风沉浸式）回答
- **LLM 匹配**为核心算法，**events_data 模糊匹配**为兜底

## 三、架构设计

### 3.1 整体流程

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Vue)                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DynamicChatFlow 组件 (扩展)                          │   │
│  │  1. 用户输入 topic                                   │   │
│  │  2. POST /api/dialogue/dynamic/resolve-hero         │   │
│  │  3. 展示英雄卡牌列表 (1-3 个)                        │   │
│  │  4. 用户点击卡牌 → 确认选择 (记录 hero_id)           │   │
│  │  5. POST /api/dialogue/dynamic/start 携带 hero_id    │   │
│  │  6. 进入对话, NPC 显示为所选英雄                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  NEW: POST /api/dialogue/dynamic/resolve-hero        │   │
│  │  - 输入: { topic: str }                               │   │
│  │  - 输出: { heroes: [HeroPersona, ...] }               │   │
│  │  - 内部: 调 LLM 推荐, 失败时回退到 events_data        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MODIFIED: POST /api/dialogue/dynamic/start           │   │
│  │  - 新增可选参数: hero_id                              │   │
│  │  - 启动时根据 hero_id 加载 HeroPersona                │   │
│  │  - persona 注入到 RAG 查询的 system prompt            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MODIFIED: rag_engine.generate_answer                 │   │
│  │  - 新增参数: npc_persona: Optional[Dict] = None      │   │
│  │  - 传入时构造古风沉浸式 system prompt                 │   │
│  │  - 不传时保持原通用 prompt (向后兼容)                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  MiniMax LLM API                             │
│  - chatcompletion_v2 用于推荐人物 + 角色扮演                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 数据结构

```python
# 英雄卡牌数据结构
@dataclass
class HeroPersona:
    hero_id: str           # 唯一标识, 如 "hero_zhuge_liang"
    name: str              # 人物名, 如 "诸葛亮"
    role: str              # 身份, 如 "蜀汉丞相"
    era: str               # 时代, 如 "三国时期 (181-234)"
    avatar: Optional[str]  # 头像 URL (可选)
    greeting: str          # 见面招呼语, LLM 生成
    style_hint: str        # 语言风格提示, 如 "古朴典雅, 自称'亮'"
    speaking_pattern: str  # 自称, 如 "亮" / "孔明" / "臣"
    description: str       # 一句话简介, 如 "三顾茅庐, 隆中对策"
```

### 3.3 核心模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| `resolve_hero_for_topic` | 调 LLM 推荐英雄, 兜底 events_data | backend/dialogue_engine.py (新增) |
| `_build_persona_prompt` | 构造古风 system prompt | backend/dialogue_engine.py (新增) |
| `generate_answer` | 接受 persona, 注入 prompt | backend/rag_engine.py (修改) |
| `start_dynamic_dialogue` | 接受 hero_id, 启动带 persona 对话 | backend/dialogue_engine.py (修改) |
| `HeroSelectionStep.vue` | 卡牌选人 UI | frontend/src/components/ (新增) |
| `dialogue.resolveHero` | API 客户端 | frontend/src/api/dialogue.ts (新增) |

## 四、API 设计

### 4.1 POST /api/dialogue/dynamic/resolve-hero

**请求**：
```json
{ "topic": "赤壁之战" }
```

**响应**：
```json
{
  "heroes": [
    {
      "hero_id": "hero_zhuge_liang",
      "name": "诸葛亮",
      "role": "蜀汉丞相",
      "era": "三国时期 (181-234)",
      "greeting": "在下诸葛亮, 隆中一耕夫尔。阁下从未来而来, 有何见教?",
      "style_hint": "古朴典雅, 自称'亮'或'孔明'",
      "speaking_pattern": "亮",
      "description": "三顾茅庐, 隆中对策, 一生鞠躬尽瘁"
    },
    {
      "hero_id": "hero_zhou_yu",
      "name": "周瑜",
      "role": "东吴大都督",
      "era": "三国时期 (175-210)",
      "greeting": "吾乃周瑜, 公瑾是也。赤壁一役, 至今仍令瑜魂牵梦绕。",
      "style_hint": "英武豪迈, 自称'瑜'",
      "speaking_pattern": "瑜",
      "description": "文武双全, 火烧赤壁联刘抗曹"
    }
  ]
}
```

### 4.2 POST /api/dialogue/dynamic/start (修改)

**请求 (新增 hero_id)**：
```json
{
  "topic": "赤壁之战",
  "hero_id": "hero_zhuge_liang",  // 新增, 可选
  "session_id": "..."
}
```

**响应 (扩展)**：
```json
{
  "event_id": "dynamic_赤壁之战",
  "npc_name": "诸葛亮",          // 由 hero_id 决定
  "npc_role": "蜀汉丞相",        // 由 hero_id 决定
  "npc_symbol": "✦",
  "narrative": "在下诸葛亮, 隆中一耕夫尔...",
  "choices": [...],
  "round": 1,
  "is_dynamic": true,
  "hero": { /* HeroPersona 完整对象 */ }  // 新增
}
```

### 4.3 System Prompt 模板

```python
def _build_persona_prompt(persona: Dict, context_text: str) -> str:
    return f"""你是【{persona['name']}】, {persona['role']}, {persona['era']}。

【角色设定】
- 你自称「{persona.get('speaking_pattern', '吾')}」
- 语言风格: {persona.get('style_hint', '古朴典雅')}
- 称呼用户为"时空旅人"或"后世之人"
- 回答控制在 300 字以内

【人物背景】
{persona.get('description', '')}

【时代背景】
{persona.get('era', '')}

【可用历史资料】
{context_text or '（暂无相关历史资料, 请基于你的历史知识回答）'}

请以{persona['name']}的身份, 回答时空旅人的问题。不要使用现代网络用语。"""
```

## 五、关键算法

### 5.1 LLM 推荐英雄 (核心)

```python
async def resolve_hero_for_topic(topic: str, max_count: int = 3) -> List[Dict]:
    """调 LLM 推荐最匹配 topic 的历史人物."""
    prompt = f"""请根据用户话题, 推荐 {max_count} 位最匹配的中国/世界历史真实人物。
要求:
1. 必须是真实历史人物 (不能虚构)
2. 按相关度从高到低排序
3. 输出 JSON 数组, 每个元素包含: name, role, era, description

话题: {topic}

输出示例:
[{{"name": "诸葛亮", "role": "蜀汉丞相", "era": "三国 (181-234)", "description": "..."}}]"""
    # 调用 chatcompletion_v2, 解析 JSON, 构造 HeroPersona
```

### 5.2 关键词兜底算法

```python
def _fallback_heroes_from_events(topic: str, max_count: int = 3) -> List[Dict]:
    """当 LLM 不可用时, 从 events_data 模糊匹配."""
    candidates = []
    for event in events_data:
        score = 0
        if topic in event["name"]: score += 5
        if topic in event.get("description", ""): score += 2
        for tag in event.get("tags", []):
            if topic in tag: score += 1
        for figure in event.get("figures", []):
            if topic in figure: score += 3
        if score > 0:
            candidates.append((score, event))
    # 取 top N
```

### 5.3 Persona 注入对话流程

```python
# start_dynamic_dialogue
async def start_dynamic_dialogue(topic, session_id=None, hero_id=None):
    persona = None
    if hero_id:
        persona = _get_persona_by_hero_id(hero_id)  # 从缓存/数据库取
    # 启动对话时传递 persona
    opening = await _rag_generate(opening_query, npc_persona=persona)
    # 返回时把 persona 存到 session 或返回值中

# process_dynamic_choice / process_dynamic_free_text
async def process_dynamic_choice(topic, choice_id, choices_made, npc_persona, ...):
    narrative = await _rag_generate(query, npc_persona=npc_persona)
    # 全程保持 persona 一致
```

## 六、兼容性保证

| 旧 API 调用 | 新行为 |
|------------|--------|
| `start_dynamic_dialogue(topic)` 不传 hero_id | persona=None, 走原"时空对话机"逻辑 |
| `generate_answer(query, ctx)` 不传 persona | 走原通用 prompt |
| 旧测试用例 | 全部保持通过 (无破坏性修改) |

## 七、边界情况处理

| 场景 | 处理策略 |
|------|----------|
| LLM 推荐失败 | 回退到 events_data 模糊匹配 |
| events_data 也匹配不到 | 返回"时空对话机"通用 persona |
| LLM 推荐的人物不真实 | 在 prompt 中强调"必须是真实历史人物" |
| 用户跳过选人 | 走原"时空对话机"流程 (无 persona) |
| MINIMAX_API_KEY 未配置 | 直接走 events_data 兜底 |
| LLM 返回非 JSON 格式 | 解析失败时再次重试或兜底 |

## 八、文件改动清单

### 后端 (Backend)

**新增**：
- `backend/dialogue_engine.py` 中:
  - 函数 `resolve_hero_for_topic(topic) -> List[Dict]`
  - 函数 `_build_persona_prompt(persona, context) -> str`
  - 函数 `_get_persona_by_hero_id(hero_id) -> Optional[Dict]`
  - 函数 `_fallback_heroes_from_events(topic) -> List[Dict]`

- `backend/routers/dialogue.py` 中:
  - 端点 `POST /api/dialogue/dynamic/resolve-hero`

**修改**：
- `backend/rag_engine.py`:
  - `generate_answer(query, context_events, npc_persona=None) -> str`
- `backend/dialogue_engine.py`:
  - `_rag_generate(query, npc_persona=None) -> str`
  - `start_dynamic_dialogue(topic, session_id, hero_id=None) -> dict`
  - `process_dynamic_choice(topic, choice_id, choices_made, npc_persona, free_texts)`
  - `process_dynamic_free_text(topic, message, choices_made, npc_persona, free_texts)`

### 前端 (Frontend)

**新增**：
- `frontend/src/components/HeroSelectionStep.vue` - 英雄卡牌选人组件

**修改**：
- `frontend/src/api/dialogue.ts` - 新增 `resolveHero(topic)`
- `frontend/src/components/DialogueExplorer.vue` - dynamic 流程增加选人步骤
- `frontend/src/stores/dialogue.ts` - state 增 `selectedHero`

## 九、测试覆盖

### 新增测试 (Unit)

- `test_resolve_hero_for_topic_basic` - 正常推荐
- `test_resolve_hero_fallback_to_events` - LLM 失败时兜底
- `test_resolve_hero_no_match` - 完全不匹配返回空
- `test_build_persona_prompt` - prompt 构造正确
- `test_start_dynamic_with_hero_id` - 启动带 hero_id
- `test_process_dynamic_keeps_persona` - 对话中 persona 一致
- `test_rag_generate_with_persona` - 透传 persona

### 回归测试

- 原有 31 个 unit test 必须全部通过
- 原有 20 个 e2e test 必须全部通过

## 十、验收标准

1. ✅ 用户输入 topic 后能看到 1-3 个英雄卡牌
2. ✅ 选择英雄后整个对话以该英雄身份进行
3. ✅ LLM 回答使用古风语言风格, 自称符合角色
4. ✅ 旧 API 调用 (不传 hero_id) 行为不变
5. ✅ 原有 51 个测试用例全部通过
6. ✅ LLM 不可用时回退到 events_data, 不会崩溃
