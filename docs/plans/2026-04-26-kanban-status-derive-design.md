# Kanban 全局状态自动推导设计

## 背景

系统有两层状态：
- **overall_status**（Task 表）：全局状态，Kanban 全局视图的列
- **local_status**（TaskAssignment 表）：每个 Location 的本地状态，Workbench 展示

之前用户在 Kanban 全局视图拖拽改 overall_status，但 Workbench 看 local_status，造成"改了没效果"的困惑。

## 设计决策

**overall_status 不再手动维护，改为由所有 local_status 自动推导。**

## 推导规则

```
所有 assignment 的 local_status → overall_status
─────────────────────────────────────────────────
全部 Completed                    → Completed
存在任一 Blocked                  → On Hold
无 Blocked + 存在 In Progress     → In Progress
无 Blocked + 存在 Completed + Pending → In Progress
全部 Pending（或无 assignment）    → Not Started
全部 Cancelled                    → Cancelled
```

优先级：Cancelled > 全部Completed > 存在Blocked > 混合 > 全部Pending

## UI 变更

### Kanban 全局视图
- 禁用拖拽（Sortable 设置 `pull: false, put: false`）
- 卡片上显示各 Location 状态小圆点（已有）
- 可选：显示进度文字如 `3/5 Completed`

### Kanban Location 视图
- 保持拖拽功能（更新 local_status）
- 拖拽后自动重新计算对应 Task 的 overall_status

### Task 编辑/详情页
- overall_status 下拉框改为只读显示
- 保留字段用于查询排序

## 推导触发点

在以下写入操作后调用推导函数：

1. Kanban Location 视图拖拽 → `update_status` 路由
2. Workbench 状态按钮 → `/workbench/status` 路由
3. Task 详情页更新 assignment → `update_assignment` 路由
4. 删除 assignment → `remove_assignment` 路由
5. 新增 assignment → `assign_location` 路由

## 实现

### 推导函数

在 `app/models.py` 或新建 `app/services/status_engine.py`：

```python
def derive_overall_status(task):
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
```

### 调用方式

在每个触发点写入完成后：
```python
task.overall_status = derive_overall_status(task)
db.session.commit()
```

## 涉及文件

- `app/models.py` 或 `app/services/status_engine.py` — 推导函数
- `app/routes/tasks.py` — update_status、update_assignment、remove_assignment、assign_location
- `app/routes/workbench.py` — status 路由
- `app/templates/tasks/kanban.html` — 全局视图禁用拖拽
- `app/templates/tasks/form.html` — overall_status 改只读
- `app/templates/tasks/detail.html` — overall_status 显示
