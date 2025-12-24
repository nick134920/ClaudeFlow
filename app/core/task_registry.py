import time


def generate_task_id(module: str) -> str:
    """
    生成任务 ID

    Args:
        module: 模块名称（如 "newprojectanalyse"）

    Returns:
        任务 ID（如 "newprojectanalyse_1735056000"）
    """
    timestamp = int(time.time())
    return f"{module}_{timestamp}"


class TaskRegistry:
    """任务 ID 注册器 - 兼容旧接口"""

    def generate_id(self, module: str) -> str:
        return generate_task_id(module)


# 全局单例
task_registry = TaskRegistry()
