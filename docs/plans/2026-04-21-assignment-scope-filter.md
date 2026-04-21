# Assignment Scope 筛选改造 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Assignment Scope 从"自动全量分配"改为"按 country 和 type 筛选后用户手动勾选 location"。

**Architecture:** 去掉 Task 模型上的 scope_type/scope_rule/scope_detail 字段，替换为 scope_country 和 scope_location_type。表单中用两个下拉筛选器 + checkbox 列表实现交互。筛选通过 HTMX 或 fetch 异步加载。

**Tech Stack:** Flask, SQLAlchemy, HTMX/fetch, Tailwind CSS, Jinja2

---

### Task 1: 更新 Task 模型

**Files:**
- Modify: `app/models.py:38-40` (scope_type, scope_rule, scope_detail → scope_country, scope_location_type)

**Step 1: 修改 Task 模型字段**

将:
```python
scope_type = db.Column(db.String(50), default="Manual")
scope_rule = db.Column(db.String(300))
scope_detail = db.Column(db.String(300))
```

改为:
```python
scope_country = db.Column(db.String(100))
scope_location_type = db.Column(db.String(50))
```

**Step 2: 修改数据库 schema**

由于项目使用 `db.create_all()`（不会修改已有表），需要手动处理数据库迁移。数据量极小（1 task, 2 locations），直接删库重建：

```bash
rm instance/tasks.db
# 下次启动 app 时 db.create_all() 会自动创建新表
```

**Step 3: 提交**

```bash
git add app/models.py
git commit -m "refactor: replace scope_type/rule/detail with scope_country/scope_location_type"
```

---

### Task 2: 更新 scope_engine.py

**Files:**
- Modify: `app/services/scope_engine.py`

**Step 1: 重写 scope_engine**

```python
from app import db
from app.models import Location


def get_filtered_locations(country=None, location_type=None):
    """根据 country 和 location_type 筛选活跃地点。两者都是可选的。"""
    query = Location.query.filter_by(is_active=True)

    if country:
        query = query.filter_by(country=country)
    if location_type:
        query = query.filter_by(location_type=location_type)

    return query.order_by(Location.location_name).all()


def get_scope_preview(country=None, location_type=None):
    """返回匹配数量和地点列表，用于预览。"""
    locations = get_filtered_locations(country, location_type)
    return {
        "locations": [
            {"id": loc.id, "name": loc.location_name, "country": loc.country, "type": loc.location_type}
            for loc in locations
        ],
    }


def get_distinct_countries():
    """获取所有活跃地点的不重复 country 列表。"""
    results = db.session.execute(
        db.text("SELECT DISTINCT country FROM location_master WHERE is_active = 1 AND country IS NOT NULL ORDER BY country")
    ).fetchall()
    return [r[0] for r in results]


def get_distinct_location_types():
    """获取所有活跃地点的不重复 location_type 列表。"""
    results = db.session.execute(
        db.text("SELECT DISTINCT location_type FROM location_master WHERE is_active = 1 AND location_type IS NOT NULL ORDER BY location_type")
    ).fetchall()
    return [r[0] for r in results]
```

**Step 2: 提交**

```bash
git add app/services/scope_engine.py
git commit -m "refactor: rewrite scope_engine for country/type filtering"
```

---

### Task 3: 更新 routes/tasks.py

**Files:**
- Modify: `app/routes/tasks.py`

**Step 1: 更新 import 和常量**

将 import 从:
```python
from app.services.scope_engine import get_matching_locations, get_scope_preview
```
改为:
```python
from app.services.scope_engine import get_filtered_locations, get_scope_preview, get_distinct_countries, get_distinct_location_types
```

去掉 `SCOPE_TYPES` 常量（不再需要）。

**Step 2: 修改 create 路由**

将 create 函数改为:

```python
@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        task = Task(
            task_name=request.form["task_name"],
            task_source=request.form.get("task_source", ""),
            stakeholder=request.form.get("stakeholder", ""),
            task_description=request.form.get("task_description", ""),
            scope_country=request.form.get("scope_country", ""),
            scope_location_type=request.form.get("scope_location_type", ""),
            task_owner=request.form.get("task_owner", ""),
            execution_model=request.form.get("execution_model", ""),
            overall_status=request.form.get("overall_status", "Not Started"),
            start_date=_parse_date(request.form.get("start_date")),
            target_date=_parse_date(request.form.get("target_date")),
            last_update=date.today(),
            link_to_file=request.form.get("link_to_file", ""),
            link_to_mail=request.form.get("link_to_mail", ""),
            task_priority=request.form.get("task_priority", "Medium"),
            comments=request.form.get("comments", ""),
        )
        db.session.add(task)
        db.session.flush()

        # 从表单获取用户勾选的 location IDs
        selected_ids = request.form.getlist("selected_locations", type=int)
        for loc_id in selected_ids:
            assignment = TaskAssignment(task_id=task.id, location_id=loc_id)
            db.session.add(assignment)

        db.session.commit()
        flash("Task created", "success")
        return redirect(url_for("tasks.detail", id=task.id))

    return render_template(
        "tasks/form.html", task=None,
        status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS,
        countries=get_distinct_countries(), location_types=get_distinct_location_types(),
    )
```

**Step 3: 修改 edit 路由**

将 edit 函数中保存 scope 的部分从:
```python
task.scope_type = request.form.get("scope_type", "Manual")
task.scope_rule = request.form.get("scope_rule", "")
task.scope_detail = request.form.get("scope_detail", "")
```
改为:
```python
task.scope_country = request.form.get("scope_country", "")
task.scope_location_type = request.form.get("scope_location_type", "")
```

edit 的 GET 渲染部分也需更新:
```python
return render_template(
    "tasks/form.html", task=task,
    status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS,
    countries=get_distinct_countries(), location_types=get_distinct_location_types(),
)
```

**Step 4: 修改 detail 路由**

去掉 `scope_types=SCOPE_TYPES`。

**Step 5: 修改 scope_preview 路由**

```python
@bp.route("/scope-preview", methods=["POST"])
def scope_preview():
    country = request.form.get("scope_country", "")
    location_type = request.form.get("scope_location_type", "")
    preview = get_scope_preview(country or None, location_type or None)
    return jsonify(preview)
```

**Step 6: 提交**

```bash
git add app/routes/tasks.py
git commit -m "refactor: update task routes for new scope filtering"
```

---

### Task 4: 重新设计表单模板 form.html

**Files:**
- Modify: `app/templates/tasks/form.html`

**Step 1: 替换 Assignment Scope 区块**

将现有的 `<!-- Assignment Scope -->` 整个区块（约第59-91行）替换为:

```html
<!-- Assignment Scope -->
<div class="mb-8">
    <h2 class="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">Assignment Scope</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
        <div>
            <label for="scope_country" class="block text-sm font-medium text-gray-700 mb-1">Country</label>
            <select id="scope_country" name="scope_country"
                class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                <option value="">-- All Countries --</option>
                {% for c in countries %}
                <option value="{{ c }}" {% if task and task.scope_country == c %}selected{% endif %}>{{ c }}</option>
                {% endfor %}
            </select>
        </div>
        <div>
            <label for="scope_location_type" class="block text-sm font-medium text-gray-700 mb-1">Location Type</label>
            <select id="scope_location_type" name="scope_location_type"
                class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                <option value="">-- All Types --</option>
                {% for t in location_types %}
                <option value="{{ t }}" {% if task and task.scope_location_type == t %}selected{% endif %}>{{ t }}</option>
                {% endfor %}
            </select>
        </div>
    </div>

    <!-- Location Checkbox List -->
    <div id="scope-locations" class="border border-gray-200 rounded-md max-h-80 overflow-y-auto">
        <div class="p-3 bg-gray-50 border-b border-gray-200 flex items-center gap-3">
            <label class="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
                <input type="checkbox" id="select-all-locations" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                Select All
            </label>
            <span id="location-count" class="text-sm text-gray-500">0 locations</span>
        </div>
        <div id="location-checkboxes" class="divide-y divide-gray-100">
            <p class="text-sm text-gray-400 p-4">Select country or type to filter locations</p>
        </div>
    </div>
</div>
```

**Step 2: 替换 extra_js 中的 script**

将整个 `{% block extra_js %}` 的 script 替换为:

```html
<script>
    const countryEl = document.getElementById('scope_country');
    const typeEl = document.getElementById('scope_location_type');
    const selectAllEl = document.getElementById('select-all-locations');
    const checkboxesContainer = document.getElementById('location-checkboxes');
    const countEl = document.getElementById('location-count');

    // 编辑模式：已分配的 location ID 列表
    {% if task and task.assignments.all() %}
    const preSelectedIds = [{% for a in task.assignments.all() %}{{ a.location_id }}{% if not loop.last %},{% endif %}{% endfor %}];
    {% else %}
    const preSelectedIds = [];
    {% endif %}

    function loadLocations() {
        const formData = new FormData();
        formData.append('scope_country', countryEl.value);
        formData.append('scope_location_type', typeEl.value);

        fetch('/tasks/scope-preview', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const locations = data.locations || [];
            countEl.textContent = locations.length + ' locations';

            if (locations.length === 0) {
                checkboxesContainer.innerHTML = '<p class="text-sm text-gray-400 p-4">No matching locations</p>';
                return;
            }

            let html = '';
            locations.forEach(loc => {
                const checked = preSelectedIds.includes(loc.id) ? 'checked' : '';
                html += `
                <label class="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 cursor-pointer">
                    <input type="checkbox" name="selected_locations" value="${loc.id}" ${checked}
                        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 location-cb">
                    <div>
                        <span class="text-sm text-gray-900">${loc.name}</span>
                        <span class="text-xs text-gray-500 ml-2">${loc.country || ''} / ${loc.type || ''}</span>
                    </div>
                </label>`;
            });
            checkboxesContainer.innerHTML = html;
            updateSelectAll();
        })
        .catch(() => {
            checkboxesContainer.innerHTML = '<p class="text-sm text-red-400 p-4">Error loading locations</p>';
        });
    }

    function updateSelectAll() {
        const boxes = document.querySelectorAll('.location-cb');
        if (boxes.length === 0) return;
        const allChecked = Array.from(boxes).every(b => b.checked);
        selectAllEl.checked = allChecked;
    }

    selectAllEl.addEventListener('change', function() {
        document.querySelectorAll('.location-cb').forEach(cb => cb.checked = this.checked);
    });

    checkboxesContainer.addEventListener('change', function(e) {
        if (e.target.classList.contains('location-cb')) {
            updateSelectAll();
        }
    });

    countryEl.addEventListener('change', loadLocations);
    typeEl.addEventListener('change', loadLocations);

    // 页面加载时立即加载
    loadLocations();
</script>
```

**Step 3: 提交**

```bash
git add app/templates/tasks/form.html
git commit -m "feat: redesign assignment scope with country/type filter and checkbox selection"
```

---

### Task 5: 更新 detail.html 显示

**Files:**
- Modify: `app/templates/tasks/detail.html:34-39`

**Step 1: 更新 Scope Info 显示**

将:
```html
<span><strong>Scope:</strong> {{ task.scope_type }}{% if task.scope_detail %} - {{ task.scope_detail }}{% endif %}</span>
```

改为:
```html
<span><strong>Scope:</strong> {{ task.scope_country or 'All Countries' }} / {{ task.scope_location_type or 'All Types' }}</span>
```

**Step 2: 提交**

```bash
git add app/templates/tasks/detail.html
git commit -m "refactor: update detail page scope display"
```

---

### Task 6: 删除旧数据库并验证

**Step 1: 删除旧数据库**

```bash
rm instance/tasks.db
```

**Step 2: 启动应用验证**

```bash
.venv/bin/python run.py
```

验证:
- 访问 `/tasks/new`，看到 Country 和 Type 下拉筛选器
- 切换筛选器，location checkbox 列表实时更新
- 勾选 location 后提交，task 创建成功
- 查看 task detail，scope 信息正确显示
- 编辑 task 时，之前勾选的 location 保持选中

**Step 3: 提交**

```bash
git add -A
git commit -m "chore: reset db for new scope schema"
```
