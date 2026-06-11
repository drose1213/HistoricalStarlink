"""验证重构后的 dialogue_engine."""
from dialogue_engine import (
    get_script,
    get_available_events,
    generate_opening,
    process_choice,
    process_free_text,
    process_post_ending,
    compute_path_signature,
)

print('=' * 60)
print('重构验证: dialogue_engine.py')
print('=' * 60)

# 1. 测试 get_available_events
print('\n[1] 测试 get_available_events()')
events = get_available_events()
print(f'  可用事件数: {len(events)}')
for ev in events:
    eid = ev['event_id']
    name = ev['npc_name']
    role = ev['npc_role']
    print(f'  - {eid}: {name} ({role})')

# 2. 测试 get_script
print('\n[2] 测试 get_script("qin_unification")')
script = get_script('qin_unification')
assert script is not None, "剧本不应为 None"
print(f'  NPC: {script["npc_name"]} ({script["npc_role"]})')
print(f'  轮次数: {len(script["rounds"])}')
print(f'  结局数: {len(script["endings"])}')
print(f'  关键词响应数: {len(script.get("keyword_responses", []))}')

# 3. 测试 generate_opening
print('\n[3] 测试 generate_opening("qin_unification")')
opening = generate_opening('qin_unification')
assert opening is not None, "开场不应为 None"
print(f'  轮次: {opening["round"]}')
print(f'  NPC: {opening["npc_name"]} ({opening["npc_role"]})')
print(f'  选项数: {len(opening["choices"])}')
print(f'  开场白前 50 字: {opening["narrative"][:50]}...')

# 4. 测试 process_choice
print('\n[4] 测试 process_choice("qin_unification", "a", 1, [])')
result = process_choice("qin_unification", "a", 1, [])
print(f'  轮次: {result["round"]}')
print(f'  mood: {result["mood"]}')
print(f'  is_ending: {result["is_ending"]}')
print(f'  narrative 前 50 字: {result["narrative"][:50]}...')

# 5. 测试 process_free_text
print('\n[5] 测试 process_free_text("qin_unification", "长城", 2, [])')
result = process_free_text("qin_unification", "长城", 2, [])
print(f'  narrative 前 50 字: {result["narrative"][:50]}...')
assert "长城" in result["narrative"] or "匈奴" in result["narrative"], "关键词响应应匹配"

# 6. 测试 process_post_ending
print('\n[6] 测试 process_post_ending("qin_unification", "再见")')
result = process_post_ending("qin_unification", "再见")
print(f'  is_ending: {result["is_ending"]}')
print(f'  narrative 前 50 字: {result["narrative"][:50]}...')

# 7. 测试 compute_path_signature
print('\n[7] 测试 compute_path_signature')
sigs = [
    ([{"mood": "agree"}, {"mood": "thoughtful"}], "A-T"),
    ([{"mood": "disagree"}, {"mood": "disagree"}], "D-D"),
    ([{"mood": "thoughtful"}, {"mood": "thoughtful"}], "T-T"),
]
for choices, expected in sigs:
    sig = compute_path_signature(choices)
    assert sig == expected, f"期望 {expected}, 实际 {sig}"
    print(f'  ✓ {sig}')

# 8. 测试 get_script 错误处理
print('\n[8] 测试 get_script("nonexistent")')
script = get_script("nonexistent")
assert script is None, "不存在的剧本应返回 None"
print('  ✓ 返回 None')

print('\n' + '=' * 60)
print('所有测试通过!')
print('=' * 60)
