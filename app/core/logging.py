import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict

from app.config import LOG_DIR, LOG_LEVEL


def _ensure_dir(path: Path) -> None:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def _get_today_str() -> str:
    """获取今天的日期字符串 YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


class RequestLogger:
    """
    请求日志记录器

    日志文件: logs/{date}/requests.log
    格式: JSON Lines
    """

    def __init__(self):
        self._logger = logging.getLogger("request")
        self._logger.setLevel(getattr(logging, LOG_LEVEL))
        self._current_date: Optional[str] = None
        self._handler: Optional[logging.FileHandler] = None

    def _ensure_handler(self) -> None:
        """确保日志处理器指向正确的日期文件"""
        today = _get_today_str()
        if self._current_date != today:
            # 移除旧处理器
            if self._handler:
                self._logger.removeHandler(self._handler)
                self._handler.close()

            # 创建新处理器
            log_dir = LOG_DIR / today
            _ensure_dir(log_dir)
            log_file = log_dir / "requests.log"

            self._handler = logging.FileHandler(log_file, encoding="utf-8")
            self._handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(self._handler)
            self._current_date = today

    def log(
        self,
        level: str,
        method: str,
        path: str,
        client_ip: str,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录请求日志

        Args:
            level: 日志级别 (INFO, WARNING, ERROR)
            method: HTTP 方法
            path: 请求路径
            client_ip: 客户端 IP
            task_id: 任务 ID（可选）
            status: 状态（可选）
            extra: 额外字段（可选）
        """
        self._ensure_handler()

        record = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "method": method,
            "path": path,
            "client_ip": client_ip,
        }
        if task_id:
            record["task_id"] = task_id
        if status:
            record["status"] = status
        if extra:
            record.update(extra)

        log_method = getattr(self._logger, level.lower(), self._logger.info)
        log_method(json.dumps(record, ensure_ascii=False))


class TaskLogger:
    """
    任务日志记录器

    日志文件: logs/{date}/tasks/{task_id}.log
    格式: 纯文本
    """

    SEPARATOR = "─" * 40

    def __init__(self, task_id: str, input_data: Dict[str, Any]):
        self.task_id = task_id
        self.input_data = input_data
        self.start_time = datetime.now()
        self.turn_count = 0
        self.tool_call_names: Dict[str, str] = {}  # call_id -> tool_name

        # 创建日志文件
        today = _get_today_str()
        log_dir = LOG_DIR / today / "tasks"
        _ensure_dir(log_dir)
        self.log_file = log_dir / f"{task_id}.log"

        # 写入头部
        self._write_header()

    def _write_header(self) -> None:
        """写入日志文件头部"""
        header = f"""{'=' * 80}
Task ID: {self.task_id}
Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Input: {json.dumps(self.input_data, ensure_ascii=False)}
{'=' * 80}

"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(header)

    def _get_timestamp(self) -> str:
        """获取当前时间戳 [HH:MM:SS]"""
        return datetime.now().strftime("[%H:%M:%S]")

    def log(self, message: str) -> None:
        """记录一条日志"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} {message}\n")

    def log_user_prompt(self, prompt: str) -> None:
        """记录用户 Prompt"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [USER] Prompt\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{prompt}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_turn_start(self) -> None:
        """记录轮次开始"""
        self.turn_count += 1
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} === TURN {self.turn_count} ===\n\n")

    def log_thinking(self, content: str) -> None:
        """记录 Claude 思考过程"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [THINKING]\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{content}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_text(self, content: str) -> None:
        """记录 Claude 文本回复"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [TEXT]\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{content}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_tool_call(self, tool_name: str, call_id: str, params: Dict[str, Any]) -> None:
        """记录工具调用"""
        self.tool_call_names[call_id] = tool_name
        params_str = json.dumps(params, ensure_ascii=False, indent=2)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [TOOL_CALL] {tool_name} ({call_id})\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{params_str}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_tool_result(
        self, call_id: str, content: Any, is_error: bool, duration: float
    ) -> None:
        """记录工具返回结果"""
        tool_name = self.tool_call_names.get(call_id, "unknown")
        status = "✗" if is_error else "✓"

        # 处理 content，可能是字符串或其他类型
        if isinstance(content, str):
            content_str = content
        else:
            content_str = json.dumps(content, ensure_ascii=False, indent=2)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [TOOL_RESULT] {tool_name} ({call_id}) {status} {duration:.1f}s\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{content_str}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_error(self, error: Exception) -> None:
        """记录完整错误堆栈"""
        import traceback
        error_trace = traceback.format_exc()
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [ERROR]\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{error_trace}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def finish(self, success: bool, error: Optional[str] = None,
               num_turns: int = 0, cost_usd: float = 0) -> None:
        """完成日志记录"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        status = "SUCCESS" if success else "FAILED"

        footer = f"""
{'=' * 80}
Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration:.1f}s
Turns: {num_turns}
Cost: ${cost_usd:.4f}
Status: {status}
"""
        if error:
            footer += f"Error: {error}\n"
        footer += "=" * 80 + "\n"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(footer)


# 全局请求日志记录器
request_logger = RequestLogger()
