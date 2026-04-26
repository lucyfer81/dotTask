from app.models import Task


def derive_overall_status(task):
    """根据 task 所有 assignment 的 local_status 推导 overall_status。

    规则优先级：
    - 无 assignment → Not Started
    - 全部 Completed → Completed
    - 全部 Pending → Not Started
    - 全部 Cancelled → Cancelled
    - 存在 Blocked → On Hold
    - 其余混合 → In Progress
    """
    assignments = task.assignments.all()
    if not assignments:
        return "Not Started"

    statuses = {a.local_status or "Pending" for a in assignments}

    if statuses == {"Completed"}:
        return "Completed"
    if statuses == {"Pending"}:
        return "Not Started"
    if statuses == {"Cancelled"}:
        return "Cancelled"
    if "Blocked" in statuses:
        return "On Hold"
    return "In Progress"


def sync_overall_status(task):
    """推导并保存 overall_status，需要在调用后自行 db.session.commit()。"""
    task.overall_status = derive_overall_status(task)
