"""
对话剧本数据加载器.

负责从 JSON 文件加载对话剧本数据, 提供查询接口,
并支持:
- 自动验证数据完整性
- 内存缓存提升性能
- 热重载数据 (无需重启服务)
- 按 event_id 快速查询
"""
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional

from .dialogue_script_validator import DialogueScriptValidator

logger = logging.getLogger(__name__)


# 默认剧本目录: backend/data/scripts/
DEFAULT_SCRIPTS_DIR = Path(__file__).parent / "scripts"


class DialogueScriptLoader:
    """对话剧本数据加载器.

    用法:
        loader = DialogueScriptLoader()
        script = loader.get_script("qin_unification")
        events = loader.get_available_events()

        # 重新加载 (用于热更新)
        loader.reload_scripts()
    """

    def __init__(
        self,
        scripts_dir: Optional[str] = None,
        enable_validation: bool = True,
        strict_validation: bool = False,
    ):
        """初始化加载器.

        Args:
            scripts_dir: 剧本目录路径, 默认为 backend/data/scripts/
            enable_validation: 是否启用数据验证, 默认 True
            strict_validation: 严格模式 (警告也视为错误), 默认 False
        """
        self.scripts_dir = Path(scripts_dir) if scripts_dir else DEFAULT_SCRIPTS_DIR
        self.enable_validation = enable_validation
        self.validator = (
            DialogueScriptValidator(strict=strict_validation)
            if enable_validation
            else None
        )

        # 剧本缓存: event_id -> script_data
        self._scripts_cache: Dict[str, dict] = {}

        # 加载锁 (避免并发加载冲突)
        self._lock = threading.RLock()

        # 初始化时加载所有剧本
        self._load_all_scripts()

    def _load_all_scripts(self):
        """加载所有剧本文件."""
        with self._lock:
            self._scripts_cache.clear()

            if not self.scripts_dir.exists():
                logger.warning(
                    f"剧本目录不存在: {self.scripts_dir}, "
                    f"请创建该目录并放入 JSON 剧本文件"
                )
                return

            # 查找所有 .json 文件
            script_files = sorted(self.scripts_dir.glob("*.json"))
            if not script_files:
                logger.warning(
                    f"剧本目录 {self.scripts_dir} 中没有找到任何 .json 文件"
                )
                return

            success_count = 0
            failed_count = 0

            for script_file in script_files:
                if self._load_single_script(script_file):
                    success_count += 1
                else:
                    failed_count += 1

            logger.info(
                f"剧本加载完成: 成功 {success_count} 个, 失败 {failed_count} 个, "
                f"总计 {len(script_files)} 个"
            )

    def _load_single_script(self, script_file: Path) -> bool:
        """加载单个剧本文件.

        Returns:
            bool: 是否加载成功.
        """
        event_id = script_file.stem

        try:
            with open(script_file, "r", encoding="utf-8") as f:
                script_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"[{event_id}] JSON 解析失败: {e}")
            return False
        except OSError as e:
            logger.error(f"[{event_id}] 读取文件失败: {e}")
            return False
        except Exception as e:
            logger.error(f"[{event_id}] 加载异常: {e}")
            return False

        # 数据验证
        if self.validator:
            is_valid, errors = self.validator.validate_script(script_data, event_id)
            if not is_valid:
                logger.error(
                    f"[{event_id}] 剧本数据验证失败, 共 {len(errors)} 个错误:"
                )
                for error in errors:
                    logger.error(f"  - {error}")
                return False

        # 存入缓存 (不包含 meta 字段, meta 仅用于元数据管理)
        if "meta" in script_data and isinstance(script_data["meta"], dict):
            # 将 meta 字段保留, 但不参与业务逻辑
            pass

        self._scripts_cache[event_id] = script_data
        logger.debug(f"成功加载剧本: {event_id}")
        return True

    def get_script(self, event_id: str) -> Optional[dict]:
        """获取指定剧本数据.

        Args:
            event_id: 事件 ID, 如 "qin_unification".

        Returns:
            剧本数据字典, 如果不存在则返回 None.
        """
        return self._scripts_cache.get(event_id)

    def get_available_events(self) -> List[dict]:
        """获取所有可用的剧本列表.

        Returns:
            [{"event_id": ..., "npc_name": ..., "npc_role": ...}, ...]
        """
        result = []
        for event_id, script in self._scripts_cache.items():
            result.append({
                "event_id": event_id,
                "npc_name": script.get("npc_name", ""),
                "npc_role": script.get("npc_role", ""),
            })
        return result

    def get_available_event_ids(self) -> List[str]:
        """获取所有可用的剧本 ID 列表."""
        return list(self._scripts_cache.keys())

    def has_script(self, event_id: str) -> bool:
        """检查剧本是否存在."""
        return event_id in self._scripts_cache

    def reload_scripts(self):
        """重新加载所有剧本数据.

        可用于热更新: 修改 JSON 文件后调用此方法, 无需重启服务.
        """
        logger.info("开始重新加载剧本数据...")
        self._load_all_scripts()
        logger.info("剧本数据重新加载完成")

    def get_stats(self) -> dict:
        """获取加载器统计信息.

        Returns:
            包含剧本数量、目录路径等信息的字典.
        """
        return {
            "scripts_dir": str(self.scripts_dir),
            "loaded_count": len(self._scripts_cache),
            "available_events": self.get_available_event_ids(),
        }


# 全局单例实例
# 整个应用共用一个加载器, 避免重复加载
_global_loader: Optional[DialogueScriptLoader] = None
_global_loader_lock = threading.Lock()


def get_script_loader() -> DialogueScriptLoader:
    """获取全局剧本加载器单例.

    Returns:
        DialogueScriptLoader 单例实例.
    """
    global _global_loader
    if _global_loader is None:
        with _global_loader_lock:
            if _global_loader is None:
                _global_loader = DialogueScriptLoader()
    return _global_loader


def reset_script_loader() -> None:
    """重置全局加载器 (主要用于测试)."""
    global _global_loader
    with _global_loader_lock:
        _global_loader = None
