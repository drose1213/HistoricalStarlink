"""
数据层: 提供历史事件、配置和对话剧本数据的统一访问入口.

包含:
- events_data: 历史事件数据 (硬编码, 后续可迁移到 JSON)
- config_data: 系统配置数据
- dialogue_script_loader: 对话剧本数据加载器 (从 JSON 加载)
- dialogue_script_validator: 对话剧本数据验证器
"""
from .dialogue_script_loader import (
    DialogueScriptLoader,
    get_script_loader,
    reset_script_loader,
)
from .dialogue_script_validator import (
    DialogueScriptValidator,
    validate_script_file,
)

__all__ = [
    "DialogueScriptLoader",
    "get_script_loader",
    "reset_script_loader",
    "DialogueScriptValidator",
    "validate_script_file",
]
