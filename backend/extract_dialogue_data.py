"""
完整数据提取脚本: 从 dialogue_engine.py 提取所有对话数据 (剧本 + 响应)
到独立的 JSON 文件中.

重构完成后可以删除此脚本.
"""
import ast
import json
from pathlib import Path


def get_function_body_var(source: str, func_name: str, var_name: str):
    """从指定函数体内提取变量值."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == var_name:
                            return ast.literal_eval(stmt.value)
    return None


def get_module_var(source: str, var_name: str):
    """从模块级作用域中提取变量值."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    return ast.literal_eval(node.value)
    return None


def main():
    backend_dir = Path(__file__).parent
    source_file = backend_dir / "dialogue_engine.py"
    scripts_dir = backend_dir / "data" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    with open(source_file, "r", encoding="utf-8") as f:
        source = f.read()

    # 提取剧本主数据
    scripts = get_module_var(source, "DIALOGUE_SCRIPTS")
    if not scripts:
        print("错误: 未找到 DIALOGUE_SCRIPTS")
        return

    # 提取对话响应数据
    keyword_responses = get_function_body_var(source, "process_free_text", "keyword_responses") or {}
    default_responses = get_function_body_var(source, "process_free_text", "default_responses") or {}
    post_responses = get_function_body_var(source, "process_post_ending", "post_responses") or {}
    post_defaults = get_function_body_var(source, "process_post_ending", "post_defaults") or {}

    print(f"剧本数: {len(scripts)}")
    print(f"keyword_responses 事件数: {len(keyword_responses)}")
    print(f"default_responses 事件数: {len(default_responses)}")
    print(f"post_responses 事件数: {len(post_responses)}")
    print(f"post_defaults 事件数: {len(post_defaults)}")
    print()

    # 写每个事件的完整 JSON
    for event_id, script_data in scripts.items():
        output_file = scripts_dir / f"{event_id}.json"

        full_data = {
            "meta": {
                "event_id": event_id,
                "version": "1.0.0",
                "description": f"{script_data.get('npc_name', '')} ({script_data.get('npc_role', '')})"
            },
            "npc_name": script_data.get("npc_name", ""),
            "npc_role": script_data.get("npc_role", ""),
            "npc_symbol": script_data.get("npc_symbol", ""),
            "opening": script_data.get("opening", ""),
            "context": script_data.get("context", ""),
            "rounds": script_data.get("rounds", []),
            "endings": script_data.get("endings", {}),
            # 自由文本响应数据
            "keyword_responses": keyword_responses.get(event_id, []),
            "default_response": default_responses.get(event_id, ""),
            "post_responses": post_responses.get(event_id, []),
            "post_default": post_defaults.get(event_id, ""),
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        size = output_file.stat().st_size
        print(f"  - {event_id}.json ({size} bytes)")

    print(f"\n完成! 共生成 {len(scripts)} 个 JSON 文件")


if __name__ == "__main__":
    main()
