"""
对话剧本数据验证器.

负责在数据加载时验证 JSON 剧本文件的完整性和正确性,
包括:
- 必需字段检查
- 数据类型验证
- 引用完整性检查 (如 next_round, choice_id 唯一性)
- 业务规则验证
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# 必需的剧本字段
REQUIRED_SCRIPT_FIELDS = [
    "npc_name", "npc_role", "opening", "context", "rounds", "endings"
]

# 必需的单轮字段
REQUIRED_ROUND_FIELDS = ["round", "choices"]

# 必需的选项字段
REQUIRED_CHOICE_FIELDS = [
    "choice_id", "text", "consequence", "timeline_change", "next_round", "mood"
]

# 必需的结局字段
REQUIRED_ENDING_FIELDS = ["historical"]

# 允许的 mood 值
VALID_MOODS = {"agree", "disagree", "thoughtful", "default"}


class DialogueScriptValidator:
    """对话剧本数据验证器.

    用法:
        validator = DialogueScriptValidator()
        is_valid, errors = validator.validate_script(script_data, event_id)
        if not is_valid:
            for error in errors:
                logger.error(error)
    """

    def __init__(self, strict: bool = False):
        """初始化验证器.

        Args:
            strict: 严格模式. True 时遇到警告也返回失败, 默认 False
                    (只对错误级别的失败返回 False, 警告记录但不阻塞).
        """
        self.strict = strict

    def validate_script(
        self, script_data: dict, event_id: str
    ) -> Tuple[bool, List[str]]:
        """验证剧本数据.

        Args:
            script_data: 剧本数据字典 (从 JSON 加载).
            event_id: 剧本 ID (用于错误信息).

        Returns:
            (is_valid, errors): 是否有效, 错误信息列表.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. 基本类型检查
        if not isinstance(script_data, dict):
            errors.append(f"[{event_id}] 剧本数据必须是字典类型, 实际: {type(script_data).__name__}")
            return False, errors

        # 2. meta 字段是可选的, 但如果有则验证
        if "meta" in script_data:
            meta = script_data["meta"]
            if not isinstance(meta, dict):
                warnings.append(f"[{event_id}] meta 字段建议为字典类型")

        # 3. 必需字段检查
        for field in REQUIRED_SCRIPT_FIELDS:
            if field not in script_data:
                errors.append(f"[{event_id}] 缺少必需字段: '{field}'")

        # 如果有必需字段缺失, 直接返回 (后续验证无意义)
        if errors:
            return False, errors

        # 4. 验证 rounds 结构
        rounds = script_data.get("rounds", [])
        if not isinstance(rounds, list):
            errors.append(f"[{event_id}] rounds 字段必须是数组类型, 实际: {type(rounds).__name__}")
        elif len(rounds) == 0:
            errors.append(f"[{event_id}] rounds 数组不能为空")
        else:
            round_errors, round_warnings = self._validate_rounds(rounds, event_id)
            errors.extend(round_errors)
            warnings.extend(round_warnings)

        # 5. 验证 endings 结构
        endings = script_data.get("endings", {})
        if not isinstance(endings, dict):
            errors.append(f"[{event_id}] endings 字段必须是字典类型")
        else:
            ending_errors, ending_warnings = self._validate_endings(endings, event_id)
            errors.extend(ending_errors)
            warnings.extend(ending_warnings)

        # 6. 验证 NPC 字段类型
        for field in ["npc_name", "npc_role", "opening", "context"]:
            value = script_data.get(field, "")
            if not isinstance(value, str):
                errors.append(f"[{event_id}] '{field}' 字段必须是字符串类型")

        # 7. 记录警告
        for warning in warnings:
            logger.warning(warning)

        is_valid = len(errors) == 0 and (not self.strict or len(warnings) == 0)
        return is_valid, errors

    def _validate_rounds(
        self, rounds: list, event_id: str
    ) -> Tuple[List[str], List[str]]:
        """验证 rounds 数组."""
        errors: List[str] = []
        warnings: List[str] = []

        seen_round_numbers = set()

        for idx, round_data in enumerate(rounds):
            if not isinstance(round_data, dict):
                errors.append(f"[{event_id}] rounds[{idx}] 必须是字典类型")
                continue

            # 必需字段检查
            for field in REQUIRED_ROUND_FIELDS:
                if field not in round_data:
                    errors.append(f"[{event_id}] rounds[{idx}] 缺少必需字段: '{field}'")

            # round 编号唯一性
            round_num = round_data.get("round")
            if round_num is not None:
                if not isinstance(round_num, int):
                    errors.append(f"[{event_id}] rounds[{idx}].round 必须是整数类型")
                else:
                    if round_num in seen_round_numbers:
                        errors.append(f"[{event_id}] 重复的 round 编号: {round_num}")
                    seen_round_numbers.add(round_num)

            # 验证 choices
            choices = round_data.get("choices", [])
            if not isinstance(choices, list):
                errors.append(f"[{event_id}] rounds[{idx}].choices 必须是数组类型")
            else:
                choice_errors, choice_warnings = self._validate_choices(
                    choices, round_num or (idx + 1), event_id
                )
                errors.extend(choice_errors)
                warnings.extend(choice_warnings)

            # narrative 字段类型检查 (虽然不是必需字段)
            for narrative_key in ["narrative", "narrative_agree", "narrative_disagree",
                                  "narrative_thoughtful", "narrative_default"]:
                if narrative_key in round_data:
                    if not isinstance(round_data[narrative_key], str):
                        errors.append(
                            f"[{event_id}] rounds[{idx}].{narrative_key} 必须是字符串类型"
                        )

        # 验证 round 编号是否从 1 开始且连续
        if seen_round_numbers:
            expected = set(range(1, max(seen_round_numbers) + 1))
            missing = expected - seen_round_numbers
            if missing:
                warnings.append(
                    f"[{event_id}] round 编号不连续, 缺失: {sorted(missing)}"
                )

        return errors, warnings

    def _validate_choices(
        self, choices: list, round_num, event_id: str
    ) -> Tuple[List[str], List[str]]:
        """验证 choices 数组."""
        errors: List[str] = []
        warnings: List[str] = []

        seen_choice_ids = set()

        for cidx, choice in enumerate(choices):
            if not isinstance(choice, dict):
                errors.append(
                    f"[{event_id}] round {round_num} 的 choices[{cidx}] 必须是字典类型"
                )
                continue

            # 必需字段检查
            for field in REQUIRED_CHOICE_FIELDS:
                if field not in choice:
                    errors.append(
                        f"[{event_id}] round {round_num} choices[{cidx}] 缺少必需字段: '{field}'"
                    )

            # choice_id 唯一性
            choice_id = choice.get("choice_id")
            if choice_id is not None:
                if not isinstance(choice_id, str):
                    errors.append(
                        f"[{event_id}] round {round_num} choices[{cidx}].choice_id 必须是字符串"
                    )
                else:
                    if choice_id in seen_choice_ids:
                        errors.append(
                            f"[{event_id}] round {round_num} 重复的 choice_id: '{choice_id}'"
                        )
                    seen_choice_ids.add(choice_id)

            # mood 值验证
            mood = choice.get("mood")
            if mood is not None and mood not in VALID_MOODS:
                errors.append(
                    f"[{event_id}] round {round_num} choice '{choice_id}' 的 mood 值 '{mood}' "
                    f"无效, 允许值: {sorted(VALID_MOODS)}"
                )

            # timeline_change 必须是布尔值
            timeline_change = choice.get("timeline_change")
            if timeline_change is not None and not isinstance(timeline_change, bool):
                errors.append(
                    f"[{event_id}] round {round_num} choice '{choice_id}' 的 timeline_change "
                    f"必须是布尔类型"
                )

            # next_round 必须是整数
            next_round = choice.get("next_round")
            if next_round is not None and not isinstance(next_round, int):
                errors.append(
                    f"[{event_id}] round {round_num} choice '{choice_id}' 的 next_round "
                    f"必须是整数类型"
                )

        return errors, warnings

    def _validate_endings(
        self, endings: dict, event_id: str
    ) -> Tuple[List[str], List[str]]:
        """验证 endings 字典."""
        errors: List[str] = []
        warnings: List[str] = []

        # 必需字段检查
        for field in REQUIRED_ENDING_FIELDS:
            if field not in endings:
                errors.append(f"[{event_id}] endings 缺少必需字段: '{field}'")

        # 所有结局必须是字符串且非空
        for key, value in endings.items():
            if not isinstance(value, str):
                errors.append(
                    f"[{event_id}] endings['{key}'] 必须是字符串类型"
                )
            elif len(value.strip()) == 0:
                warnings.append(
                    f"[{event_id}] endings['{key}'] 是空字符串"
                )

        # 建议有 altered 结局
        if "altered" not in endings:
            warnings.append(
                f"[{event_id}] 建议提供 'altered' 结局 (平行时间线)"
            )

        return errors, warnings


def validate_script_file(file_path: str) -> Tuple[bool, List[str]]:
    """便捷函数: 验证单个剧本文件.

    Args:
        file_path: JSON 剧本文件路径.

    Returns:
        (is_valid, errors): 是否有效, 错误信息列表.
    """
    path = Path(file_path)
    event_id = path.stem

    try:
        with open(path, "r", encoding="utf-8") as f:
            script_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"[{event_id}] JSON 解析失败: {e}"]
    except Exception as e:
        return False, [f"[{event_id}] 读取文件失败: {e}"]

    validator = DialogueScriptValidator()
    return validator.validate_script(script_data, event_id)
