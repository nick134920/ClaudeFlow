import threading
from datetime import date
from typing import Dict


class TaskRegistry:
    """任务 ID 注册器 - 生成 {module}-{sequence:03d} 格式的任务 ID"""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {}  # module -> counter
        self._current_date: date = date.today()

    def _reset_if_new_day(self) -> None:
        """如果日期变化，重置所有计数器"""
        today = date.today()
        if today != self._current_date:
            self._counters.clear()
            self._current_date = today

    def generate_id(self, module: str) -> str:
        """
        生成任务 ID

        Args:
            module: 模块名称（如 "summarize"）

        Returns:
            任务 ID（如 "summarize-001"）
        """
        with self._lock:
            self._reset_if_new_day()
            self._counters[module] = self._counters.get(module, 0) + 1
            return f"{module}-{self._counters[module]:03d}"


# 全局单例
task_registry = TaskRegistry()
