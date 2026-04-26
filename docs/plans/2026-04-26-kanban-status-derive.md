# Kanban 全局状态自动推导 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** overall_status 不再手动维护，改为由所有 local_status 自动推导。Kanban 全局视图禁用拖拽。

**Architecture:** 新建 `app/services/status_engine.py` 放推导函数，在每个写入 local_status 的路由末尾调用。前端 Kanban 全局视图禁用 SortableJS 拖拽，编辑表单的 overall_status 改为只读。

**Tech Stack:** Python/Flask, SQLAlchemy, SortableJS, HTMX, Jinja2

---

### Task 1: 创建推导函数 status_engine.py

**Files:**
- Create: `app/services/status_engine.py`

**Step 1: 创建推导函数文件**

```python
# app/services/status_engine.py
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
```

**Step 2: 用 Python 验证函数逻辑**

运行:
```bash
cd /home/ubuntu/my-repos/dotTask && .venv/bin/python -c "
from app import create_app, db
from app.models import Task
from app.services.status_engine import derive_overall_status

app = create_app()
with app.app_context():
    for t in Task.query.all():
        assignments = t.assignments.all()
        statuses = {a.local_status or 'Pending' for a in assignments}
        derived = derive_overall_status(t)
        match = '✓' if derived == t.overall_status else '✗'
        print(f'{match} Task {t.id}: current={t.overall_status}, derived={derived}, locals={statuses}')
"
```

Expected: 输出每个 task 的当前状态和推导状态的对比。

**Step 3: Commit**

```bash
git add app/services/status_engine.py
git commit -m "feat: add overall_status derivation engine"
```

---

### Task 2: 在所有写入 local_status 的路由中调用推导

**Files:**
- Modify: `app/routes/tasks.py:183-205` (update_status)
- Modify: `app/routes/tasks.py:228-244` (update_assignment)
- Modify: `app/routes/tasks.py:247-253` (remove_assignment)
- Modify: `app/routes/tasks.py:208-225` (assign_location)
- Modify: `app/routes/workbench.py:105-127` (update_status)

**Step 1: 修改 tasks.py — update_status 路由**

在文件顶部添加 import:
```python
from app.services.status_engine import sync_overall_status
```

修改 `update_status` 路由 (line 183-205)，在两个 db.session.commit() 之前添加推导调用：

- 全局状态分支 (loc_id 为空时): 保留整体状态更新逻辑不变（这个分支处理的是 HT-Request 的 status_menu 场景，需要保留）
- 本地状态分支 (loc_id 有值时): 在 `assignment.local_status = new_status` 后、`db.session.commit()` 前，添加:
```python
sync_overall_status(assignment.task)
```

**Step 2: 修改 tasks.py — update_assignment 路由**

在 `update_assignment` 路由 (line 228-244) 中，在 `db.session.commit()` 前添加:
```python
sync_overall_status(assignment.task)
```

**Step 3: 修改 tasks.py — remove_assignment 路由**

在 `remove_assignment` 路由 (line 247-253) 中，在 `db.session.delete(assignment)` 后、`db.session.commit()` 前添加:
```python
task = assignment.task
```
在 commit 后不再引用已删除对象，但 sync_overall_status 需要在 delete 之前调用:
```python
sync_overall_status(assignment.task)
```

**Step 4: 修改 tasks.py — assign_location 路由**

在 `assign_location` 路由 (line 208-225) 中，在 `db.session.commit()` 前添加:
```python
sync_overall_status(task)
```

**Step 5: 修改 workbench.py — update_status 路由**

添加 import:
```python
from app.services.status_engine import sync_overall_status
```

在 `update_status` 路由中，在 `db.session.commit()` 前添加:
```python
sync_overall_status(assignment.task)
```

**Step 6: 用浏览器验证**

启动服务，在 Workbench 中点击状态按钮，确认 overall_status 被正确更新。

**Step 7: Commit**

```bash
git add app/routes/tasks.py app/routes/workbench.py
git commit -m "feat: sync overall_status on every local_status write"
```

---

### Task 3: Kanban 全局视图禁用拖拽

**Files:**
- Modify: `app/templates/tasks/kanban.html:125-155`

**Step 1: 修改 initSortable 函数**

在 `kanban.html` 的 `initSortable` 函数中，根据 `isFiltered` 变量决定是否启用拖拽：

将 Sortable 初始化代码改为：
```javascript
function initSortable() {
    document.querySelectorAll('.kanban-column').forEach(function(col) {
        if (col._sortable) return;
        col._sortable = new Sortable(col, {
            group: isFiltered ? 'kanban' : false,  // 全局视图禁用拖拽
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            animation: 200,
            sort: isFiltered,  // 全局视图禁用排序
            onEnd: function(evt) {
                if (!isFiltered) return;  // 全局视图不应触发
                var taskId = evt.item.dataset.taskId;
                var newStatus = evt.to.dataset.status;
                evt.item.classList.add('ring-2', 'ring-blue-400');
                setTimeout(function() { evt.item.classList.remove('ring-2', 'ring-blue-400'); }, 800);
                if (locationId) {
                    htmx.ajax('POST', '/tasks/' + taskId + '/status', {
                        values: { local_status: newStatus, location_id: locationId },
                        target: 'body',
                        swap: 'none'
                    });
                }
            }
        });
    });
}
```

**Step 2: 用浏览器验证**

- 打开 Kanban 全局视图，确认卡片无法拖拽（光标不应显示 grab）
- 切换到 Location 视图，确认拖拽仍然可用
- 在 Location 视图拖拽后，切回全局视图确认 overall_status 已更新

**Step 3: Commit**

```bash
git add app/templates/tasks/kanban.html
git commit -m "feat: disable drag on kanban global view, overall_status auto-derived"
```

---

### Task 4: 编辑表单 overall_status 改为只读

**Files:**
- Modify: `app/templates/tasks/form.html:119-127`

**Step 1: 修改编辑表单**

编辑模式时 overall_status 改为只读显示，新建模式时保留默认值 `Not Started`。

将 form.html 的 overall_status 部分 (line 119-127) 改为：
```html
<div>
    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Overall Status</label>
    {% if task %}
    <input type="text" value="{{ task.overall_status }}" disabled
        class="w-full px-3 py-2 border border-gray-200 dark:border-cc-border rounded-md text-sm bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed">
    <input type="hidden" name="overall_status" value="{{ task.overall_status }}">
    {% else %}
    <input type="hidden" name="overall_status" value="Not Started">
    <div class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Auto-derived from location statuses</div>
    {% endif %}
</div>
```

**Step 2: 同时清理 tasks.py 中 edit 路由对 overall_status 的写入**

编辑 `tasks.py` 的 `edit` 路由 (line 143-171)，移除:
```python
task.overall_status = request.form.get("overall_status", "Not Started")
```
改为不改 overall_status（它已经由推导自动管理）。

**Step 3: 用浏览器验证**

- 打开 Task 编辑页面，确认 overall_status 显示为只读
- 打开新建 Task 页面，确认显示 "Auto-derived from location statuses"

**Step 4: Commit**

```bash
git add app/templates/tasks/form.html app/routes/tasks.py
git commit -m "feat: make overall_status read-only in edit form"
```

---

### Task 5: 补回历史数据的 overall_status

**Files:**
- Create: one-time script (不提交)

**Step 1: 运行一次迁移脚本，把现有所有 task 的 overall_status 重新推导**

```bash
cd /home/ubuntu/my-repos/dotTask && .venv/bin/python -c "
from app import create_app, db
from app.models import Task
from app.services.status_engine import derive_overall_status

app = create_app()
with app.app_context():
    tasks = Task.query.all()
    updated = 0
    for t in tasks:
        derived = derive_overall_status(t)
        if t.overall_status != derived:
            print(f'  Task {t.id} \"{t.task_name[:40]}\": {t.overall_status} → {derived}')
            t.overall_status = derived
            updated += 1
    db.session.commit()
    print(f'Done. Updated {updated}/{len(tasks)} tasks.')
"
```

**Step 2: 用浏览器验证**

打开 Kanban 全局视图和 Workbench，确认状态一致。

---

### Task 6: 端到端验证

**Step 1: 场景 1 — Workbench 改状态**

1. 打开 Workbench，选择一个 Location + Task
2. 点击状态按钮改为 Completed
3. 切到 Kanban 全局视图，确认该 Task 移到了正确的列
4. 如果该 Task 还有其他 Location 不是 Completed，确认它在 In Progress 列

**Step 2: 场景 2 — Kanban Location 视图拖拽**

1. 打开 Kanban，选择一个 Location
2. 拖拽一个 Task 到 Completed 列
3. 切到 Kanban 全局视图，确认 overall_status 正确推导
4. 切到 Workbench，确认 local_status 是 Completed

**Step 3: 场景 3 — Kanban 全局视图不可拖拽**

1. 打开 Kanban 全局视图（不选 Location）
2. 尝试拖拽卡片，确认无法拖动
3. 光标应为默认样式而非 grab

**Step 4: 清理**

```bash
rm -f /home/ubuntu/my-repos/dotTask/*.png
```
