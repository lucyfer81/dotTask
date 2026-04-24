# Workbench 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 dotTask 新增 `/workbench` 沉浸式执行台页面，通过双向联动选择器 + 状态大按钮 + 日志录入实现快速任务操作。

**Architecture:** 新增 Flask Blueprint `workbench`，复用 TaskAssignment 模型，task_log 字段用 Markdown checklist 格式存储行动项。前端 HTMX 局部刷新 + Alpine.js 处理快捷键。

**Tech Stack:** Flask, SQLAlchemy, HTMX 2.0.4, Alpine.js, Tailwind CSS, Jinja2

---

### Task 1: 添加 Alpine.js CDN 和 Workbench 导航入口

**Files:**
- Modify: `app/templates/base.html:25-27,40-46`

**Step 1: 在 base.html 添加 Alpine.js CDN**

在 `htmx.org@2.0.4` script 标签之后添加 Alpine.js：

```html
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

注意：Alpine.js 需要 `defer` 属性，放在 body 末尾或带 defer 都可以。

**Step 2: 在导航栏添加 Workbench 链接**

在 Kanban 链接之后、Locations 链接之前，添加 Workbench 导航项：

```html
<a href="/workbench" class="nav-link {% if '/workbench' in request.path %}text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400{% else %}text-gray-600 dark:text-gray-300{% endif %} inline-flex items-center px-1 pt-1 text-sm font-medium hover:text-blue-600 dark:hover:text-blue-400">Workbench</a>
```

**Step 3: 启动服务验证导航栏显示 Workbench**

Run: `bash taskmgr.sh restart`
打开浏览器访问 `http://localhost:5000`，确认导航栏出现 Workbench 链接。点击确认跳转到 404（此时路由还未创建）。

**Step 4: Commit**

```bash
git add app/templates/base.html
git commit -m "feat: add Alpine.js CDN and Workbench nav link"
```

---

### Task 2: 创建 Workbench Blueprint 并注册

**Files:**
- Create: `app/routes/workbench.py`
- Modify: `app/__init__.py:25-33`

**Step 1: 创建 workbench Blueprint 骨架**

创建 `app/routes/workbench.py`：

```python
from flask import Blueprint, render_template
from app.models import Location, Task, TaskAssignment
from app import db

bp = Blueprint("workbench", __name__, url_prefix="/workbench")


@bp.route("/")
def index():
    locations = Location.query.filter_by(is_active=True).order_by(Location.location_name).all()
    tasks = Task.query.order_by(Task.task_name).all()
    return render_template("workbench/index.html", locations=locations, tasks=tasks)
```

**Step 2: 在 app factory 注册 Blueprint**

修改 `app/__init__.py`，在 `data_io` 注册之后添加：

```python
    from .routes import workbench
    app.register_blueprint(workbench.bp)
```

**Step 3: 创建最小模板文件**

创建目录 `app/templates/workbench/`，创建 `index.html`：

```html
{% extends "base.html" %}

{% block title %}Workbench - APAC Task Manager{% endblock %}

{% block content %}
<div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Workbench</h1>
    <p class="text-gray-500 dark:text-gray-300">Workbench is under construction.</p>
</div>
{% endblock %}
```

**Step 4: 重启验证**

Run: `bash taskmgr.sh restart`
访问 `http://localhost:5000/workbench`，确认页面正常显示。

**Step 5: Commit**

```bash
git add app/routes/workbench.py app/__init__.py app/templates/workbench/index.html
git commit -m "feat: create workbench blueprint with minimal page"
```

---

### Task 3: 创建 task_log 解析工具

**Files:**
- Create: `app/services/task_log_parser.py`

**Step 1: 实现 parse_task_log 函数**

创建 `app/services/task_log_parser.py`：

```python
"""Parse task_log text field into structured entries and checklist items.

Expected format in task_log:
    ## 2026-04-24 14:30
    Some log content here.

    ## Action Items
    - [x] Completed task
    - [ ] Pending task

    ## 2026-04-23 09:00
    Earlier log entry.
"""
import re


def parse_task_log(text):
    """Parse task_log text into structured data.

    Returns dict with:
        entries: list of {"timestamp": str, "content": str}
        checklist: list of {"text": str, "done": bool}
    """
    if not text or not text.strip():
        return {"entries": [], "checklist": []}

    entries = []
    checklist = []

    lines = text.split("\n")
    current_entry = None

    for line in lines:
        ts_match = re.match(r"^##\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", line)
        if ts_match:
            if current_entry:
                entries.append(current_entry)
            current_entry = {"timestamp": ts_match.group(1), "content": ""}
            continue

        check_match = re.match(r"^-\s*\[([ xX])\]\s*(.+)$", line)
        if check_match:
            checklist.append({
                "text": check_match.group(2).strip(),
                "done": check_match.group(1).lower() == "x",
            })
            continue

        if current_entry is not None:
            current_entry["content"] += line + "\n"

    if current_entry:
        entries.append(current_entry)

    for entry in entries:
        entry["content"] = entry["content"].strip()

    entries.reverse()

    return {"entries": entries, "checklist": checklist}


def rebuild_task_log(entries, checklist):
    """Rebuild task_log text from structured data.

    Args:
        entries: list of {"timestamp": str, "content": str} (newest first, will be reversed)
        checklist: list of {"text": str, "done": bool}

    Returns:
        str: formatted task_log text
    """
    parts = []

    for entry in reversed(entries):
        parts.append(f"## {entry['timestamp']}")
        if entry["content"]:
            parts.append(entry["content"])
        parts.append("")

    if checklist:
        parts.append("## Action Items")
        for item in checklist:
            mark = "x" if item["done"] else " "
            parts.append(f"- [{mark}] {item['text']}")
        parts.append("")

    return "\n".join(parts).strip()


def add_log_entry(text, content):
    """Add a new timestamped log entry to task_log text.

    Returns updated task_log text.
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    parsed = parse_task_log(text)
    parsed["entries"].insert(0, {"timestamp": timestamp, "content": content})

    return rebuild_task_log(parsed["entries"], parsed["checklist"])


def toggle_checklist_item(text, item_text):
    """Toggle a checklist item's done status.

    Returns updated task_log text.
    """
    parsed = parse_task_log(text)
    for item in parsed["checklist"]:
        if item["text"] == item_text:
            item["done"] = not item["done"]
            break
    return rebuild_task_log(parsed["entries"], parsed["checklist"])
```

**Step 2: 用 Python 验证解析器**

Run: `cd /home/ubuntu/my-repos/dotTask && .venv/bin/python -c "
from app.services.task_log_parser import parse_task_log, add_log_entry, toggle_checklist_item

sample = '''## 2026-04-24 14:30
已完成补丁分发。

## Action Items
- [x] 检查系统版本
- [ ] 验证重启结果

## 2026-04-23 09:00
开始执行升级任务。'''

result = parse_task_log(sample)
print('Entries:', len(result['entries']))
print('Checklist:', len(result['checklist']))
print('First entry ts:', result['entries'][0]['timestamp'])
print('Checklist done:', [c['done'] for c in result['checklist']])

updated = toggle_checklist_item(sample, '验证重启结果')
print('After toggle:')
print(updated)
"`
Expected: 2 entries, 2 checklist items, first entry timestamp is "2026-04-24 14:30", toggle works correctly.

**Step 3: Commit**

```bash
git add app/services/task_log_parser.py
git commit -m "feat: add task_log Markdown parser with checklist support"
```

---

### Task 4: 实现 Workbench 路由（联动选择器 + 内容加载 + 日志 + 状态）

**Files:**
- Modify: `app/routes/workbench.py` (full rewrite)

**Step 1: 完整实现 workbench 路由**

重写 `app/routes/workbench.py`：

```python
from flask import Blueprint, render_template, request
from datetime import date
from app.models import Location, Task, TaskAssignment
from app import db
from app.services.task_log_parser import parse_task_log, add_log_entry, toggle_checklist_item
from app.dropdowns import get_options

bp = Blueprint("workbench", __name__, url_prefix="/workbench")


@bp.route("/")
def index():
    locations = Location.query.filter_by(is_active=True).order_by(Location.location_name).all()
    tasks = Task.query.order_by(Task.task_name).all()
    local_statuses = get_options("local_statuses")
    return render_template(
        "workbench/index.html",
        locations=locations,
        tasks=tasks,
        local_statuses=local_statuses,
    )


@bp.route("/options")
def options():
    """Return linked dropdown <option> HTML fragment."""
    opt_type = request.args.get("type", "")
    filter_id = request.args.get("filter_id", type=int)

    if opt_type == "task" and filter_id:
        assignments = TaskAssignment.query.filter_by(location_id=filter_id).all()
        task_ids = [a.task_id for a in assignments]
        tasks = Task.query.filter(Task.id.in_(task_ids)).order_by(Task.task_name).all() if task_ids else []
        return render_template("workbench/partials/_options.html", items=tasks, value_attr="id", label_attr="task_name")

    if opt_type == "location" and filter_id:
        assignments = TaskAssignment.query.filter_by(task_id=filter_id).all()
        loc_ids = [a.location_id for a in assignments]
        locations = Location.query.filter(Location.id.in_(loc_ids)).order_by(Location.location_name).all() if loc_ids else []
        return render_template("workbench/partials/_options.html", items=locations, value_attr="id", label_attr="location_name")

    return ""


@bp.route("/content")
def content():
    """Return left+right pane content for selected assignment."""
    location_id = request.args.get("location_id", type=int)
    task_id = request.args.get("task_id", type=int)

    if not location_id or not task_id:
        return render_template("workbench/partials/_empty.html")

    assignment = TaskAssignment.query.filter_by(
        location_id=location_id, task_id=task_id
    ).first()

    if not assignment:
        return render_template("workbench/partials/_empty.html")

    parsed = parse_task_log(assignment.task_log)
    local_statuses = get_options("local_statuses")

    return render_template(
        "workbench/partials/_content.html",
        assignment=assignment,
        parsed=parsed,
        local_statuses=local_statuses,
    )


@bp.route("/log", methods=["POST"])
def add_log():
    """Add a log entry and return updated content panes."""
    assignment_id = request.form.get("assignment_id", type=int)
    assignment = TaskAssignment.query.get_or_404(assignment_id)

    log_content = request.form.get("content", "").strip()
    toggle_item = request.form.get("toggle_item", "").strip()

    if log_content:
        assignment.task_log = add_log_entry(assignment.task_log, log_content)

    if toggle_item:
        assignment.task_log = toggle_checklist_item(assignment.task_log, toggle_item)

    assignment.last_update = date.today()
    db.session.commit()

    parsed = parse_task_log(assignment.task_log)
    local_statuses = get_options("local_statuses")

    return render_template(
        "workbench/partials/_content.html",
        assignment=assignment,
        parsed=parsed,
        local_statuses=local_statuses,
    )


@bp.route("/status", methods=["POST"])
def update_status():
    """Update assignment status and return updated content panes."""
    assignment_id = request.form.get("assignment_id", type=int)
    assignment = TaskAssignment.query.get_or_404(assignment_id)

    new_status = request.form.get("local_status", "")
    local_statuses = get_options("local_statuses")
    if new_status in local_statuses:
        old_status = assignment.local_status or "Pending"
        assignment.local_status = new_status
        assignment.last_update = date.today()
        status_msg = f"Status changed: {old_status} → {new_status}"
        assignment.task_log = add_log_entry(assignment.task_log, status_msg)
        db.session.commit()

    parsed = parse_task_log(assignment.task_log)

    return render_template(
        "workbench/partials/_content.html",
        assignment=assignment,
        parsed=parsed,
        local_statuses=local_statuses,
    )
```

**Step 2: 重启验证路由不报错**

Run: `bash taskmgr.sh restart`
访问 `http://localhost:5000/workbench`，确认页面正常加载（模板还不完整，会报错，这是预期的）。

**Step 3: Commit**

```bash
git add app/routes/workbench.py
git commit -m "feat: implement workbench routes (options, content, log, status)"
```

---

### Task 5: 创建 Workbench 主页面模板

**Files:**
- Rewrite: `app/templates/workbench/index.html`

**Step 1: 创建完整的 index.html**

```html
{% extends "base.html" %}

{% block title %}Workbench - APAC Task Manager{% endblock %}

{% block content %}
<div x-data="workbench()" class="space-y-4" x-init="init()">
    <!-- Top: Dual Pivot Selector -->
    <div class="bg-white dark:bg-cc-card shadow-sm rounded-lg border border-gray-200 dark:border-cc-border p-4">
        <div class="flex flex-wrap items-center gap-4">
            <div class="flex-1 min-w-[200px]">
                <label class="block text-xs font-medium text-gray-500 dark:text-gray-300 mb-1">Location</label>
                <select id="wb-location" name="location_id"
                        hx-get="/workbench/options?type=task"
                        hx-vals='js:{filter_id: document.getElementById("wb-location").value}'
                        hx-target="#wb-task"
                        hx-swap="innerHTML"
                        hx-trigger="change"
                        class="w-full text-sm border border-gray-300 dark:border-cc-border rounded-md px-3 py-2 bg-white dark:bg-cc-card text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">-- Select Location --</option>
                    {% for loc in locations %}
                    <option value="{{ loc.id }}">{{ loc.location_name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="flex-1 min-w-[200px]">
                <label class="block text-xs font-medium text-gray-500 dark:text-gray-300 mb-1">Task</label>
                <select id="wb-task" name="task_id"
                        hx-get="/workbench/options?type=location"
                        hx-vals='js:{filter_id: document.getElementById("wb-task").value}'
                        hx-target="#wb-location"
                        hx-swap="innerHTML"
                        hx-trigger="change"
                        class="w-full text-sm border border-gray-300 dark:border-cc-border rounded-md px-3 py-2 bg-white dark:bg-cc-card text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">-- Select Task --</option>
                    {% for task in tasks %}
                    <option value="{{ task.id }}">{{ task.task_name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="flex-shrink-0 pt-5">
                <button class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                        hx-get="/workbench/content"
                        hx-vals='js:{location_id: document.getElementById("wb-location").value, task_id: document.getElementById("wb-task").value}'
                        hx-target="#wb-content"
                        hx-swap="innerHTML"
                        hx-trigger="click">
                    Load
                </button>
            </div>
        </div>
    </div>

    <!-- Bottom: Dual Pane Content -->
    <div id="wb-content">
        <div class="bg-white dark:bg-cc-card shadow-sm rounded-lg border border-gray-200 dark:border-cc-border p-8 text-center text-gray-400 dark:text-gray-500">
            Select a location and task above to begin.
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
function workbench() {
    return {
        init() {
            // Listen for content load to auto-focus textarea
            document.body.addEventListener('htmx:afterSwap', function(event) {
                if (event.detail.target.id === 'wb-content') {
                    var textarea = document.getElementById('wb-log-input');
                    if (textarea) textarea.focus();
                }
            });
        }
    };
}
</script>
{% endblock %}
```

**Step 2: 重启验证**

Run: `bash taskmgr.sh restart`
访问 `http://localhost:5000/workbench`，确认页面显示两个下拉框和 Load 按钮。

**Step 3: Commit**

```bash
git add app/templates/workbench/index.html
git commit -m "feat: create workbench main page with dual pivot selectors"
```

---

### Task 6: 创建 Workbench 局部模板

**Files:**
- Create: `app/templates/workbench/partials/_options.html`
- Create: `app/templates/workbench/partials/_empty.html`
- Create: `app/templates/workbench/partials/_content.html`
- Create: `app/templates/workbench/partials/_timeline.html`
- Create: `app/templates/workbench/partials/_checklist.html`

**Step 1: 创建 _options.html**

```html
<option value="">-- Select --</option>
{% for item in items %}
<option value="{{ item[value_attr] }}">{{ item[label_attr] }}</option>
{% endfor %}
```

**Step 2: 创建 _empty.html**

```html
<div class="bg-white dark:bg-cc-card shadow-sm rounded-lg border border-gray-200 dark:border-cc-border p-8 text-center text-gray-400 dark:text-gray-500">
    No matching assignment found. Select a valid location-task combination.
</div>
```

**Step 3: 创建 _checklist.html**

```html
{% if parsed.checklist %}
<div class="mb-4">
    <div class="flex items-center justify-between mb-2">
        <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wide">Action Items</h3>
        <span class="text-xs text-gray-400 dark:text-gray-500">
            {{ parsed.checklist | selectattr('done') | list | length }}/{{ parsed.checklist | length }}
        </span>
    </div>
    {% set done_count = parsed.checklist | selectattr('done') | list | length %}
    {% set total = parsed.checklist | length %}
    {% if total > 0 %}
    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mb-3">
        <div class="bg-green-500 h-1.5 rounded-full transition-all duration-300" style="width: {{ (done_count / total * 100) | int }}%"></div>
    </div>
    {% endif %}
    <div class="space-y-1">
        {% for item in parsed.checklist %}
        <label class="flex items-center gap-2 text-sm py-0.5 cursor-pointer group">
            <input type="checkbox"
                   {% if item.done %}checked{% endif %}
                   hx-post="/workbench/log"
                   hx-vals='{"assignment_id": "{{ assignment.id }}", "toggle_item": "{{ item.text }}"}'
                   hx-target="#wb-content"
                   hx-swap="innerHTML"
                   class="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:bg-gray-700">
            <span class="{% if item.done %}line-through text-gray-400 dark:text-gray-500{% else %}text-gray-700 dark:text-gray-200{% endif %}">
                {{ item.text }}
            </span>
        </label>
        {% endfor %}
    </div>
</div>
{% endif %}
```

**Step 4: 创建 _timeline.html**

```html
{% if parsed.entries %}
<div>
    <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wide mb-3">Timeline</h3>
    <div class="relative pl-4 border-l-2 border-gray-200 dark:border-cc-border space-y-3">
        {% for entry in parsed.entries %}
        <div class="relative">
            <div class="absolute -left-[1.3rem] top-1 w-2.5 h-2.5 rounded-full bg-blue-400 dark:bg-blue-500 border-2 border-white dark:border-cc-card"></div>
            <div class="text-xs font-mono text-gray-400 dark:text-gray-500">{{ entry.timestamp }}</div>
            {% if entry.content %}
            <div class="text-sm text-gray-700 dark:text-gray-300 mt-0.5 whitespace-pre-wrap">{{ entry.content }}</div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
```

**Step 5: 创建 _content.html（核心双栏布局）**

```html
<div class="grid grid-cols-1 lg:grid-cols-5 gap-4" x-data="{ logContent: '' }">
    <!-- Left: Context Pane (2/5) -->
    <div class="lg:col-span-2 bg-white dark:bg-cc-card shadow-sm rounded-lg border border-gray-200 dark:border-cc-border p-4 space-y-4 max-h-[calc(100vh-12rem)] overflow-y-auto">
        <!-- Assignment Header -->
        <div class="pb-3 border-b border-gray-200 dark:border-cc-border">
            <div class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {{ assignment.location.location_name }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {{ assignment.task.task_name }}
            </div>
        </div>

        <!-- Checklist -->
        {% include "workbench/partials/_checklist.html" %}

        <!-- Timeline -->
        {% include "workbench/partials/_timeline.html" %}
    </div>

    <!-- Right: Action Pane (3/5) -->
    <div class="lg:col-span-3 bg-white dark:bg-cc-card shadow-sm rounded-lg border border-gray-200 dark:border-cc-border p-4 space-y-5">
        <!-- Status Buttons -->
        <div>
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wide mb-2">Status</h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {% for status in local_statuses %}
                {% if status != 'Cancelled' %}
                {% set is_active = (assignment.local_status or 'Pending') == status %}
                {% set color_map = {
                    'Pending': 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600',
                    'In Progress': 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800/60',
                    'Blocked': 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-800/60',
                    'Completed': 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800/60',
                } %}
                <button hx-post="/workbench/status"
                        hx-vals='{"assignment_id": "{{ assignment.id }}", "local_status": "{{ status }}"}'
                        hx-target="#wb-content"
                        hx-swap="innerHTML"
                        class="px-3 py-3 rounded-lg text-sm font-medium transition-all duration-150 border-2
                               {% if is_active %}border-{{ status | lower | replace(' ', '-') }} ring-2 ring-offset-1 {{ color_map.get(status, 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300') }}{% else %}border-transparent {{ color_map.get(status, 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300') }}{% endif %}">
                    {{ status }}
                </button>
                {% endif %}
                {% endfor %}
            </div>
        </div>

        <!-- Log Input -->
        <div>
            <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wide mb-2">Quick Log</h3>
            <textarea id="wb-log-input"
                      x-model="logContent"
                      x-ref="logInput"
                      @keydown.ctrl.enter="if(logContent.trim()) { $el.closest('form').querySelector('button[type=submit]').click() }"
                      placeholder="Ctrl+Enter to submit..."
                      class="w-full px-3 py-3 text-sm border border-gray-200 dark:border-cc-border rounded-lg bg-gray-50 dark:bg-cc-bg text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      rows="4"></textarea>
            <form hx-post="/workbench/log"
                  hx-target="#wb-content"
                  hx-swap="innerHTML"
                  class="mt-2 flex items-center justify-between">
                <input type="hidden" name="assignment_id" value="{{ assignment.id }}">
                <input type="hidden" name="content" x-model="logContent">
                <span class="text-xs text-gray-400 dark:text-gray-500">Ctrl+Enter to submit</span>
                <button type="submit"
                        :disabled="!logContent.trim()"
                        class="px-4 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed">
                    Submit
                </button>
            </form>
        </div>

        <!-- Auxiliary Info -->
        <div class="pt-3 border-t border-gray-200 dark:border-cc-border">
            <div class="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
                {% if assignment.it_name %}
                <span>IT: {{ assignment.it_name }}{% if assignment.it_role %} ({{ assignment.it_role }}){% endif %}</span>
                {% endif %}
                {% if assignment.location.it_manager %}
                <span>Manager: {{ assignment.location.it_manager }}</span>
                {% endif %}
                {% if assignment.location.primary_it_contact %}
                <span>Contact: {{ assignment.location.primary_it_contact }}</span>
                {% endif %}
            </div>
            {% if assignment.task.file_links or assignment.task.mail_links %}
            <div class="flex gap-3 mt-2">
                {% for link in assignment.task.file_links %}
                <a href="{{ link.url }}" target="_blank" rel="noopener"
                   class="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                    </svg>
                    {{ link.name }}
                </a>
                {% endfor %}
                {% for link in assignment.task.mail_links %}
                <a href="{{ link.url }}" target="_blank" rel="noopener"
                   class="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                    </svg>
                    {{ link.name }}
                </a>
                {% endfor %}
            </div>
            {% endif %}
        </div>
    </div>
</div>
```

**Step 6: 重启并验证**

Run: `bash taskmgr.sh restart`
访问 `http://localhost:5000/workbench`，选择一个 Location 和 Task，点击 Load，确认双栏内容正确显示。

**Step 7: Commit**

```bash
git add app/templates/workbench/
git commit -m "feat: add workbench partial templates (content, checklist, timeline)"
```

---

### Task 7: 改进联动选择器交互

**Files:**
- Modify: `app/templates/workbench/index.html` (选择器区域)
- Modify: `app/routes/workbench.py` (options 路由)

**Step 1: 使选择器变更时自动加载内容**

修改 index.html 的选择器区域——在选择器的 `hx-trigger` 中添加自定义事件，使其在过滤完对方下拉框后也自动加载内容：

将 Location select 修改为：

```html
<select id="wb-location" name="location_id"
        hx-get="/workbench/options?type=task"
        hx-vals='js:{filter_id: document.getElementById("wb-location").value}'
        hx-target="#wb-task"
        hx-swap="innerHTML"
        hx-trigger="change"
        onchange="setTimeout(function(){ loadContent(); }, 50)"
        ...>
```

同理修改 Task select。添加 `loadContent` 函数到 extra_js：

```javascript
function loadContent() {
    var locId = document.getElementById('wb-location').value;
    var taskId = document.getElementById('wb-task').value;
    if (locId && taskId) {
        htmx.ajax('GET', '/workbench/content', {
            target: '#wb-content',
            swap: 'innerHTML',
            values: { location_id: locId, task_id: taskId }
        });
    }
}
```

**Step 2: 重启并验证联动**

Run: `bash taskmgr.sh restart`
测试：选择 Location → Task 下拉自动过滤 → 手动选 Task → 内容自动加载。

**Step 3: Commit**

```bash
git add app/templates/workbench/index.html
git commit -m "feat: auto-load content on selector change"
```

---

### Task 8: 添加 Workbench 专用 CSS 样式

**Files:**
- Modify: `app/static/css/main.css`

**Step 1: 在 main.css 末尾追加 workbench 样式**

```css
/* === Workbench === */
.wb-active-btn {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}
.dark .wb-active-btn {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
```

样式保持最少——状态按钮的激活态已在 Tailwind 类中处理，这里的 CSS 仅补充少量动画效果。

**Step 2: 重启验证**

Run: `bash taskmgr.sh restart`
确认 workbench 页面样式正常，暗色模式下无视觉问题。

**Step 3: Commit**

```bash
git add app/static/css/main.css
git commit -m "feat: add workbench CSS styles"
```

---

### Task 9: 集成测试与验证

**Step 1: 重启服务**

Run: `bash taskmgr.sh restart`

**Step 2: 完整流程测试**

在浏览器中执行以下操作：

1. 访问 `http://localhost:5000/workbench`
2. 确认导航栏 Workbench 高亮
3. 选择一个 Location → 确认 Task 下拉框被过滤
4. 选择一个 Task → 确认内容自动加载
5. 确认左栏显示：Assignment Header + Checklist（如有） + Timeline（如有）
6. 确认右栏显示：状态按钮（当前状态高亮） + 日志输入框 + 辅助信息
7. 点击不同状态按钮 → 确认状态切换、Timeline 新增状态变更记录
8. 在日志输入框输入文字 → 点击 Submit → 确认 Timeline 顶部新增记录、输入框清空
9. 按 Ctrl+Enter → 确认同上效果
10. 勾选/取消 checklist 条目 → 确认更新持久化
11. 切换暗色模式 → 确认所有元素可读

**Step 3: 修复发现的问题**

根据测试结果修复任何视觉或功能问题。

**Step 4: Final Commit**

```bash
git add -A
git commit -m "fix: workbench integration fixes"
```
