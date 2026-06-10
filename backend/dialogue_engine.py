"""
对话引擎 - 预置剧本实现的对话式历史探索
不依赖LLM，使用预置的多轮对话剧本和关键词匹配

数据层:
  - 对话剧本数据已迁移到 backend/data/scripts/*.json
  - 通过 DialogueScriptLoader 加载, 本文件只保留业务逻辑
  - 内容编辑者直接编辑 JSON 文件即可修改对话内容
"""
import uuid
import re
import logging
from typing import Optional

# 支持两种导入方式: 1) 作为 backend 包的一部分 (from .data import ...)
#                 2) 独立模块 (从 data 模块直接导入)
try:
    from .data import get_script_loader
except ImportError:
    from data import get_script_loader  # type: ignore

logger = logging.getLogger(__name__)

# 4 维画像关键词词典
EMPATHY_KEYWORDS = ("百姓", "民生", "共情", "仁慈", "仁政", "爱民", "民苦", "苍生")
REFORM_KEYWORDS = ("变法", "改革", "新制", "新政", "改制", "革新")
CONSERVATIVE_KEYWORDS = ("传统", "稳定", "延续", "守成", "祖制", "祖训")
RADICAL_KEYWORDS = ("彻底", "全盘", "推翻", "打倒", "革命", "暴力")


# === 数据访问层 ===
# 数据从 data/scripts/*.json 加载, 通过 get_script_loader() 访问

# 兼容旧代码: 保留一个空的 dict 引用, 旧调用方应改为 get_script() 函数
DIALOGUE_SCRIPTS = {}


def get_script(event_id: str) -> Optional[dict]:
    """从 JSON 数据文件加载剧本数据.

    Returns:
        剧本数据字典, 如果事件 ID 不存在则返回 None.
    """
    return get_script_loader().get_script(event_id)


def get_available_events() -> list:
    """获取所有可用的事件列表."""
    return get_script_loader().get_available_events()


def generate_opening(event_id: str) -> Optional[dict]:
    script = get_script(event_id)
    if not script:
        return None

    first_round = script["rounds"][0] if script["rounds"] else None
    if not first_round:
        return None

    return {
        "npc_name": script["npc_name"],
        "npc_role": script["npc_role"],
        "npc_symbol": script["npc_symbol"],
        "context": script["context"],
        "narrative": first_round["narrative"],
        "choices": first_round.get("choices", []),
        "round": 1
    }


def process_choice(
    event_id: str,
    choice_id: str,
    current_round: int,
    choices_made: list
) -> Optional[dict]:
    script = get_script(event_id)
    if not script:
        return None

    total_rounds = len(script["rounds"])

    if current_round >= total_rounds:
        return _build_ending(script, choices_made)

    current_round_data = script["rounds"][current_round - 1]

    selected_choice = None
    for c in current_round_data.get("choices", []):
        if c["choice_id"] == choice_id:
            selected_choice = c
            break

    if not selected_choice:
        return None

    new_mood = selected_choice.get("mood", "default")
    timeline_change = selected_choice.get("timeline_change", False)

    new_choices_made = choices_made + [{
        "round": current_round,
        "choice_id": choice_id,
        "choice_text": selected_choice["text"],
        "consequence": selected_choice["consequence"],
        "mood": new_mood
    }]

    next_round_num = current_round + 1

    if next_round_num > total_rounds:
        return _build_ending(script, new_choices_made)

    next_round_data = script["rounds"][next_round_num - 1]

    mood_key = f"narrative_{new_mood}"
    narrative = next_round_data.get(mood_key) or next_round_data.get("narrative_default", "")

    choices = next_round_data.get("choices", [])

    if not choices:
        ending = _build_ending(script, new_choices_made)
        full_narrative = f"*{selected_choice['consequence']}*\n\n{narrative}\n\n---\n\n{ending['narrative']}"
        path_sig = ending.get("path_signature", "")
        return {
            "narrative": full_narrative,
            "choices": [],
            "round": next_round_num,
            "timeline_change": timeline_change,
            "mood": new_mood,
            "is_ending": True,
            "ending_type": ending.get("ending_type", "historical"),
            "path_signature": path_sig,
            "partial_match": ending.get("partial_match", False),
            "cumulative_impact": compute_dimension_scores(new_choices_made),
            "predicted_endings": predict_endings(script, path_sig, top_n=2),
            "choices_summary": ending.get("choices_summary", [])
        }

    path_sig = compute_path_signature(new_choices_made)
    return {
        "narrative": f"*{selected_choice['consequence']}*\n\n{narrative}",
        "choices": choices,
        "round": next_round_num,
        "timeline_change": timeline_change,
        "mood": new_mood,
        "is_ending": False,
        "path_signature": path_sig,
        "cumulative_impact": compute_dimension_scores(new_choices_made),
        "predicted_endings": predict_endings(script, path_sig, top_n=2),
    }


def process_free_text(event_id: str, message: str, current_round: int, choices_made: list) -> dict:
    script = get_script(event_id)
    if not script:
        return {
            "narrative": "时空的干扰太大了，你的话无法传达给对方。",
            "choices": [],
            "round": current_round,
            "timeline_change": False,
            "is_ending": False
        }

    msg_lower = message.lower()

    # 从剧本数据中读取 keyword_responses 和 default_response
    # 数据已迁移到 data/scripts/*.json
    keyword_responses = script.get("keyword_responses", [])
    responses = keyword_responses  # 兼容后续代码

    for keywords, response in responses:
        for kw in keywords:
            if kw in msg_lower:
                return {
                    "narrative": response,
                    "choices": _get_current_round_choices(script, current_round),
                    "round": current_round,
                    "timeline_change": False,
                    "is_ending": False
                }

    # 默认响应从剧本数据中读取
    default_response = script.get("default_response", "对方似乎没有完全理解你的话，但仍在认真倾听。")

    return {
        "narrative": default_response,
        "choices": _get_current_round_choices(script, current_round),
        "round": current_round,
        "timeline_change": False,
        "is_ending": False
    }


def _get_current_round_choices(script: dict, current_round: int) -> list:
    if current_round <= len(script["rounds"]):
        return script["rounds"][current_round - 1].get("choices", [])
    return []


def process_post_ending(event_id: str, message: str) -> dict:
    script = get_script(event_id)
    if not script:
        return {
            "narrative": "时空的裂缝已经闭合，你无法再与过去对话。",
            "choices": [],
            "round": 0,
            "is_ending": True,
        }

    # 从剧本数据中读取 post_responses 和 post_default
    # 数据已迁移到 data/scripts/*.json
    post_responses = script.get("post_responses", [])

    msg_lower = message.lower()
    responses = post_responses

    for keywords, response in responses:
        for kw in keywords:
            if kw in msg_lower:
                return {
                    "narrative": response,
                    "choices": [],
                    "round": 0,
                    "is_ending": True,
                }

    # 默认结束响应从剧本数据中读取
    post_default = script.get("post_default", "时空的裂缝正在愈合。这段对话已经成为了历史的一部分，而你，即将回到属于自己的时代。")

    return {
        "narrative": post_default,
        "choices": [],
        "round": 0,
        "is_ending": True,
    }


def _build_ending(script: dict, choices_made: list, free_texts: Optional[list] = None) -> dict:
    """构造最终结局.

    三段式匹配:
    1. 路径签名完全匹配 script["endings"]
    2. 前缀匹配 (按长度倒序) - 标记 partial_match
    3. RAG 兜底 - 调 rag_engine 生成
    4. 最后回退到 "historical"
    """
    path_sig = compute_path_signature(choices_made or [])
    endings = script.get("endings") or {}

    ending_type = None
    ending_text = None
    is_partial = False

    if path_sig and path_sig in endings:
        ending_type = path_sig
        ending_text = endings[path_sig]
    elif path_sig:
        # 前缀匹配: 找最长的 ending key 是 path_sig 前缀
        candidates = [k for k in endings.keys() if k != "historical" and path_sig.startswith(k)]
        if candidates:
            candidates.sort(key=len, reverse=True)
            ending_type = candidates[0]
            ending_text = endings[ending_type]
            is_partial = True
            ending_text = f"{ending_text}\n\n（部分匹配：完整路径签名 {path_sig} 无对应结局，使用了 {ending_type} 结局作为参考）"

    if ending_text is None:
        # 尝试 RAG 兜底
        rag_text = _rag_fallback_ending_sync(script.get("npc_name") or script.get("event_id", ""), path_sig, choices_made, free_texts)
        if rag_text:
            ending_type = "rag_fallback"
            ending_text = rag_text
        else:
            ending_type = "historical"
            ending_text = endings.get("historical", "历史的车轮滚滚向前，你的时空对话已结束。")

    has_timeline_change = any(
        c.get("timeline_change") or c.get("mood") == "thoughtful"
        for c in (choices_made or [])
    )

    choices_summary = []
    for c in (choices_made or []):
        choices_summary.append({
            "round": c.get("round"),
            "text": c.get("choice_text", ""),
            "consequence": c.get("consequence", "")
        })

    return {
        "narrative": ending_text,
        "choices": [],
        "round": 0,
        "timeline_change": has_timeline_change,
        "mood": "ending",
        "is_ending": True,
        "ending_type": ending_type,
        "path_signature": path_sig,
        "partial_match": is_partial,
        "choices_summary": choices_summary,
    }


def _rag_fallback_ending_sync(event_key: str, path_sig: str, choices_made: Optional[list], free_texts: Optional[list]) -> Optional[str]:
    """RAG 兜底: 调 rag_engine.full_rag_query 生成 1 段结局, 截断到 280 字.

    rag_engine 内部是 async + 远端 API, 这里只尝试同步快速路径:
    1. 先尝试 import rag_engine.full_rag_query
    2. 失败 / 无 API key → 返回 None
    """
    try:
        from .rag_engine import full_rag_query
    except Exception:
        return None
    try:
        import asyncio
        # 在已有 event loop 中跑会失败, 用 try 兜底
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在 async 上下文中, 跳过 (由调用方异步处理)
                return None
        except RuntimeError:
            pass
        query = f"{event_key} 的平行时间线结局, 基于用户选择 {path_sig}"
        result = asyncio.run(full_rag_query(query, top_k=3))
        answer = (result or {}).get("answer", "")
        if not answer:
            return None
        return answer[:280]
    except Exception as e:
        logger.warning("RAG fallback ending failed: %s", e)
        return None


def compute_path_signature(choices_made: Optional[list]) -> str:
    """把 choices 列表压缩为 mood 序列签名 (A/D/T/N)."""
    if not choices_made:
        return ""
    mapping = {"agree": "A", "disagree": "D", "thoughtful": "T"}
    parts = []
    for c in choices_made:
        mood = c.get("mood") or ""
        parts.append(mapping.get(mood, "N"))
    return "-".join(parts)


def compute_dimension_scores(choices_made: Optional[list], free_texts: Optional[list] = None) -> dict:
    """计算 4 维画像 0-100 分."""
    scores = {"reform": 0, "conservative": 0, "empathy": 0, "radicalism": 0}
    for c in (choices_made or []):
        mood = c.get("mood") or ""
        if mood == "thoughtful":
            scores["reform"] += 10
        elif mood == "agree":
            scores["conservative"] += 10
        elif mood == "disagree":
            scores["radicalism"] += 10
    for text in (free_texts or []):
        if not text:
            continue
        for kw in EMPATHY_KEYWORDS:
            if kw in text:
                scores["empathy"] += 8
        for kw in REFORM_KEYWORDS:
            if kw in text:
                scores["reform"] += 5
        for kw in CONSERVATIVE_KEYWORDS:
            if kw in text:
                scores["conservative"] += 5
        for kw in RADICAL_KEYWORDS:
            if kw in text:
                scores["radicalism"] += 8
    # 截断到 0-100
    for k in scores:
        scores[k] = max(0, min(100, scores[k]))
    return scores


def predict_endings(script: dict, path_sig: str, top_n: int = 2) -> list:
    """预测当前路径最可能命中的结局 key 列表 (前 top_n 个)."""
    endings = script.get("endings") or {}
    if not path_sig:
        return list(endings.keys())[:top_n]
    keys = [k for k in endings.keys() if k != "historical" and path_sig.startswith(k)]
    keys.sort(key=len, reverse=True)
    return keys[:top_n]


def has_timeline_change(mood: str, timeline_change: bool) -> bool:
    return timeline_change or mood == "thoughtful"


def calculate_timeline_branches(choices_made: list) -> list:
    branches = []
    for c in choices_made:
        if c.get("mood") == "thoughtful" or c.get("timeline_change"):
            branches.append({
                "branch_point": f"Round {c['round']}",
                "original": "Following the historical path",
                "altered": c.get("consequence", "A different choice was made"),
                "choice_text": c.get("choice_text", "")
            })
    return branches


# === 任意话题 dynamic 模式 ===
# 不依赖预置剧本, 由 RAG 引擎动态生成 NPC 回应与结局.
# event_id 形如 "dynamic_<slug>", 与 DIALOGUE_SCRIPTS 并行.

MAX_DYNAMIC_ROUNDS = 10
DYNAMIC_NPC_NAME = "时空对话机"
DYNAMIC_NPC_ROLE = "全知观测者"
DYNAMIC_NPC_SYMBOL = "✦"

_DEFAULT_DYNAMIC_OPENING = (
    "你好，时空旅人。我是【时空对话机】——不拘泥于任何剧本的历史观测者。\n\n"
    "你提到了「{topic}」。这听起来是一个值得探索的话题。\n"
    "请告诉我：你想从哪里开始？是对起源的好奇，对人物的评价，还是对未来的畅想？"
)
_DEFAULT_DYNAMIC_FALLBACK = "时空之门暂时无法回应，请稍后再试。"

# 3 个可复用选项, 让对话有节奏感
_DYNAMIC_CHOICES = [
    {"choice_id": "explore_origin", "text": "我想了解它的起源", "mood": "thoughtful"},
    {"choice_id": "ask_impact",    "text": "它对后世有什么影响？", "mood": "thoughtful"},
    {"choice_id": "free",          "text": "我想自己提问", "mood": "agree"},
]


# === Hero 英雄卡牌相关函数 ===
def _fallback_heroes_from_events(topic: str, max_count: int = 3) -> list:
    """当 LLM 不可用时, 从 events_data 模糊匹配候选人物.

    Args:
        topic: 用户输入的话题
        max_count: 最多返回的英雄数

    Returns:
        Hero 列表: [{"name": ..., "role": ..., "era": ..., "description": ..., "figures": [...]}]
    """
    if not topic or not topic.strip():
        return []
    try:
        from .data.events_data import events_data
    except ImportError:
        from data.events_data import events_data  # type: ignore

    candidates = []
    topic_lower = topic.strip().lower()
    for event in events_data:
        score = 0.0
        if topic in event.get("name", ""):
            score += 5.0
        if topic in event.get("description", ""):
            score += 2.0
        for tag in event.get("tags", []):
            if topic in tag:
                score += 1.0
        for figure in event.get("figures", []):
            if figure and topic in figure:
                score += 3.0
        if score > 0:
            candidates.append((score, event))

    candidates.sort(key=lambda x: x[0], reverse=True)
    result = []
    for score, event in candidates[:max_count]:
        year = event.get("year", 0)
        if year < 0:
            year_str = f"公元前{abs(year)}年"
        else:
            year_str = f"公元{year}年"
        figures = event.get("figures", [])
        primary = figures[0] if figures else event.get("name", "未知")
        result.append({
            "name": primary,
            "role": event.get("name", "历史人物"),
            "era": f"{year_str} ({event.get('region', '')})",
            "description": event.get("description", "")[:200],
            "figures": figures,
            "source_event": event.get("id"),
        })
    return result


async def _call_llm_for_hero_recommendation(topic: str, max_count: int = 3) -> list:
    """调 LLM 推荐与 topic 最相关的历史人物.

    Returns:
        推荐的人物列表, 解析失败返回 [].
    """
    import os
    import json
    import httpx

    api_key = os.getenv("MINIMAX_API_KEY", "")
    if not api_key:
        return []

    prompt = f"""请根据用户话题, 推荐 {max_count} 位最匹配的真实历史人物 (中国或世界历史).

要求:
1. 必须是真实历史人物, 不能虚构或神话人物
2. 按相关度从高到低排序
3. 输出严格的 JSON 数组, 不要包含其他文字

每个元素的字段:
- name: 人物姓名
- role: 身份/职务
- era: 时代 (如"三国时期 (181-234)" 或 "19世纪 (1736-1819)")
- description: 一句话简介 (50字以内)

话题: {topic}

输出示例:
[{{"name": "诸葛亮", "role": "蜀汉丞相", "era": "三国时期 (181-234)", "description": "三顾茅庐, 隆中对策"}}]"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.minimax.chat/v1/text/chatcompletion_v2",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "MiniMax-M2.1",
                    "messages": [
                        {"role": "system", "content": "你是历史人物推荐助手, 只输出 JSON 数组."},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            # 提取 JSON 数组 (可能被 ```json 包裹)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            parsed = json.loads(content)
            if isinstance(parsed, list):
                # 过滤无效项
                valid = [p for p in parsed if isinstance(p, dict) and p.get("name")]
            return valid[:max_count]
    except Exception as e:
        logger.warning(f"LLM hero recommendation failed: {e}")
    return []


async def resolve_hero_for_topic(topic: str, max_count: int = 3) -> dict:
    """为话题推荐英雄卡牌列表. LLM 优先, 失败时回退到 events_data.

    Returns:
        {
            "heroes": [
                {
                    "hero_id": str,        # 唯一标识
                    "name": str,
                    "role": str,
                    "era": str,
                    "greeting": str,      # 见面招呼
                    "style_hint": str,    # 语言风格
                    "speaking_pattern": str,  # 自称
                    "description": str,
                }
            ],
            "source": "llm" | "fallback" | "empty"
        }
    """
    if not topic or not topic.strip():
        return {"heroes": [], "source": "empty"}

    # 1. 先尝试 LLM 推荐
    llm_results = await _call_llm_for_hero_recommendation(topic.strip(), max_count)

    heroes = []
    if llm_results:
        for idx, item in enumerate(llm_results):
            name = item.get("name", "").strip()
            if not name:
                continue
            hero_id = f"hero_{_slugify_topic(name)}_{idx}"
            role = item.get("role", "历史人物")
            era = item.get("era", "")
            desc = item.get("description", "")
            heroes.append({
                "hero_id": hero_id,
                "name": name,
                "role": role,
                "era": era,
                "greeting": _generate_default_greeting(name, role),
                "style_hint": "古朴典雅, 使用符合古人身份的语言",
                "speaking_pattern": _infer_speaking_pattern(name),
                "description": desc,
            })
        if heroes:
            return {"heroes": heroes, "source": "llm"}

    # 2. 回退到 events_data
    fallback = _fallback_heroes_from_events(topic.strip(), max_count)
    if fallback:
        for idx, item in enumerate(fallback):
            name = item.get("name", "").strip()
            if not name:
                continue
            hero_id = f"hero_{_slugify_topic(name)}_fb{idx}"
            heroes.append({
                "hero_id": hero_id,
                "name": name,
                "role": item.get("role", "历史人物"),
                "era": item.get("era", ""),
                "greeting": _generate_default_greeting(name, item.get("role", "")),
                "style_hint": "古朴典雅, 使用符合古人身份的语言",
                "speaking_pattern": _infer_speaking_pattern(name),
                "description": item.get("description", ""),
            })
        return {"heroes": heroes, "source": "fallback"}

    # 3. 完全无匹配
    return {"heroes": [], "source": "empty"}


def _generate_default_greeting(name: str, role: str) -> str:
    """根据人物生成默认招呼语."""
    if not name:
        return "你好, 时空旅人."
    if any(kw in role for kw in ["皇帝", "王", "皇", "帝"]):
        return f"朕乃{name}, 何方人士, 竟闯入朕的面前?"
    if any(kw in role for kw in ["将军", "元帅", "都督"]):
        return f"某乃{name}, 不知阁下有何见教?"
    if any(kw in role for kw in ["丞相", "臣", "宰相"]):
        return f"在下{name}, 阁下从未来而来, 有何指教?"
    if any(kw in role for kw in ["发明家", "科学家"]):
        return f"你好, 我是{name}, 欢迎来到我的工作室!"
    return f"吾乃{name}, 时空旅人, 你我有何可谈?"


def _infer_speaking_pattern(name: str) -> str:
    """根据人物名推断自称. 简单规则, 实际由 LLM 自由发挥."""
    # 三国类常见自称
    if name in ["诸葛亮", "孔明"]:
        return "亮"
    if name in ["刘备"]:
        return "备"
    if name in ["曹操", "孟德"]:
        return "操"
    if name in ["周瑜", "公瑾"]:
        return "瑜"
    if name in ["关羽", "云长"]:
        return "关某"
    # 帝王类
    if name in ["秦始皇", "嬴政", "赢政"]:
        return "寡人"
    if name in ["汉武帝"]:
        return "朕"
    if name in ["刘邦"]:
        return "朕"
    if name in ["唐太宗", "李世民"]:
        return "朕"
    # 默认
    if len(name) == 2:
        return name[1]  # 取名讳
    return "吾"


def _slugify_topic(topic: str) -> str:
    """把任意 topic 字符串规整成可作为 event_id 后缀的 slug."""
    if not topic:
        return "unknown"
    # 只保留中英文和数字, 其余转下划线, 截断 32 字符
    import re as _re
    s = _re.sub(r"[^\w\u4e00-\u9fff]+", "_", topic.strip().lower())
    return s[:32] or "unknown"


def build_dynamic_event_id(topic: str) -> str:
    return f"dynamic_{_slugify_topic(topic)}"


def _keyword_fallback_text(query: str, top_k: int = 3, max_chars: int = 500) -> str:
    """当 RAG 不可用时的关键词兜底: 从 HISTORY_EVENTS 找最相关, 拼一段说明."""
    try:
        from .rag_engine import _keyword_search
        results = _keyword_search(query, top_k=top_k)
    except Exception:
        return _DEFAULT_DYNAMIC_FALLBACK
    if not results:
        return f"关于「{query}」我暂时没有找到对应的历史记录, 但这是一个值得深思的问题。"
    lines = [f"关于「{query}」, 我从历史中检索到以下可能相关的事件:"]
    for r in results[:top_k]:
        ev = r.get("event", {}) if isinstance(r.get("event"), dict) else {}
        name = ev.get("name") or r.get("name") or "未知事件"
        year = ev.get("year")
        year_str = f"（公元前{abs(year)}年）" if isinstance(year, int) and year < 0 else (f"（公元{year}年）" if isinstance(year, int) else "")
        desc = ev.get("importance")
        lines.append(f"• {name}{year_str} — 重要性 {desc}/10")
    text = "\n".join(lines)
    return text[:max_chars]


async def _rag_generate(query: str, top_k: int = 3, max_chars: int = 500) -> str:
    """统一 RAG 调用入口, 失败/不可用时回退到关键词检索."""
    try:
        from .rag_engine import full_rag_query, _keyword_search
    except Exception as e:
        logger.warning("rag_engine import failed: %s", e)
        return _keyword_fallback_text(query, top_k=top_k, max_chars=max_chars)
    try:
        result = await full_rag_query(query, top_k=top_k)
        answer = (result or {}).get("answer", "")
        if answer:
            return answer[:max_chars]
    except Exception as e:
        logger.warning("full_rag_query failed: %s", e)
    # 兜底
    return _keyword_fallback_text(query, top_k=top_k, max_chars=max_chars)


async def start_dynamic_dialogue(topic: str, session_id: Optional[str] = None) -> dict:
    """为任意 topic 开启一个 dynamic 时空对话.

    Returns:
        {
            "event_id": "dynamic_<slug>",
            "npc_name": "时空对话机",
            "npc_role": "全知观测者",
            "npc_symbol": "✦",
            "context": "...",
            "narrative": <opening>,
            "choices": [...3 options...],
            "round": 1,
            "topic": <原始 topic>,
            "is_dynamic": True,
        }
    """
    if not topic or not topic.strip():
        raise ValueError("topic 不能为空")
    topic = topic.strip()[:120]  # 截断防止滥用
    event_id = build_dynamic_event_id(topic)
    opening_query = f"话题: {topic} 的背景介绍与历史脉络"
    opening = await _rag_generate(opening_query, top_k=3, max_chars=500)
    if not opening or opening == _DEFAULT_DYNAMIC_FALLBACK:
        opening = _DEFAULT_DYNAMIC_OPENING.format(topic=topic)
    return {
        "event_id": event_id,
        "npc_name": DYNAMIC_NPC_NAME,
        "npc_role": DYNAMIC_NPC_ROLE,
        "npc_symbol": DYNAMIC_NPC_SYMBOL,
        "context": f"用户选择探索的话题: {topic}",
        "narrative": opening,
        "choices": _DYNAMIC_CHOICES,
        "round": 1,
        "topic": topic,
        "is_dynamic": True,
    }


async def process_dynamic_choice(
    topic: str,
    choice_id: str,
    choices_made: list,
    free_texts: Optional[list] = None,
) -> dict:
    """处理 dynamic 对话中的选择. 返回 NPC 回应 + 累计画像."""
    if not topic or not topic.strip():
        raise ValueError("topic 不能为空")

    mood_map = {c["choice_id"]: c["mood"] for c in _DYNAMIC_CHOICES}
    selected = next((c for c in _DYNAMIC_CHOICES if c["choice_id"] == choice_id), None)
    if not selected:
        return {
            "narrative": "时空对话机没有理解这个选择, 请重新选择。",
            "choices": _DYNAMIC_CHOICES,
            "round": (len(choices_made) or 0) + 1,
            "timeline_change": False,
            "is_ending": False,
            "mood": "default",
        }
    mood = mood_map.get(choice_id, "default")
    new_choices = (choices_made or []) + [{
        "round": (len(choices_made) or 0) + 1,
        "choice_id": choice_id,
        "choice_text": selected["text"],
        "mood": mood,
    }]
    next_round = len(new_choices) + 1
    # 走到 MAX_DYNAMIC_ROUNDS 之后进入 ending
    is_last = next_round > MAX_DYNAMIC_ROUNDS
    if not is_last:
        query = f"话题 {topic}, 用户选择了「{selected['text']}」, 接下来如何回应?"
        narrative = await _rag_generate(query, top_k=3, max_chars=500)
    else:
        narrative = "时空对话机的能量即将耗尽, 让我给你一个总结性回答。"

    path_sig = compute_path_signature(new_choices)
    return {
        "narrative": narrative,
        "choices": [] if is_last else _DYNAMIC_CHOICES,
        "round": next_round,
        "timeline_change": mood == "thoughtful",
        "mood": mood,
        "is_ending": is_last,
        "is_dynamic": True,
        "path_signature": path_sig,
        "cumulative_impact": compute_dimension_scores(new_choices, free_texts),
    }


async def process_dynamic_free_text(
    topic: str,
    message: str,
    choices_made: list,
    free_texts: Optional[list] = None,
) -> dict:
    """处理 dynamic 对话中的自由文本."""
    if not topic or not topic.strip():
        raise ValueError("topic 不能为空")
    if not message or not message.strip():
        return {
            "narrative": "时空对话机等待你的提问。",
            "choices": _DYNAMIC_CHOICES,
            "round": (len(choices_made) or 0) + 1,
            "timeline_change": False,
            "is_ending": False,
        }
    new_choices = choices_made or []
    new_free_texts = (free_texts or []) + [message.strip()[:500]]
    query = f"话题 {topic}, 用户说: {message.strip()[:200]}"
    narrative = await _rag_generate(query, top_k=3, max_chars=500)
    path_sig = compute_path_signature(new_choices)
    return {
        "narrative": narrative,
        "choices": _DYNAMIC_CHOICES,
        "round": (len(new_choices) or 0) + 1,
        "timeline_change": False,
        "mood": "default",
        "is_ending": False,
        "is_dynamic": True,
        "path_signature": path_sig,
        "cumulative_impact": compute_dimension_scores(new_choices, new_free_texts),
    }


async def _build_dynamic_ending(
    topic: str,
    choices_made: Optional[list] = None,
    free_texts: Optional[list] = None,
) -> dict:
    """构造 dynamic 对话结局. 调用 RAG 生成 1 段总结性结局, 截断 280 字."""
    summary_query = f"话题 {topic} 的总结与深远影响"
    text = await _rag_generate(summary_query, top_k=3, max_chars=280)
    if not text or text == _DEFAULT_DYNAMIC_FALLBACK:
        text = f"关于「{topic}」的探索告一段落。无论你从哪个角度切入, 历史与思想的多样性, 才是时空穿越真正馈赠给你的礼物。"

    has_change = any(
        c.get("mood") in ("thoughtful", "disagree") or c.get("timeline_change")
        for c in (choices_made or [])
    )
    path_sig = compute_path_signature(choices_made or [])
    return {
        "narrative": text,
        "choices": [],
        "round": 0,
        "timeline_change": has_change,
        "mood": "ending",
        "is_ending": True,
        "is_dynamic": True,
        "ending_type": "rag_dynamic",
        "path_signature": path_sig,
        "partial_match": False,
        "cumulative_impact": compute_dimension_scores(choices_made or [], free_texts or []),
    }
