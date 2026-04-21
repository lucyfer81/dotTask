# YAML 下拉框配置 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将所有硬编码下拉框常量迁移到 `config/dropdowns.yaml`，统一管理选项数据，并将 location_type 表单从文本输入改为下拉框。

**Architecture:** 新建 YAML 配置文件存放所有下拉框选项，新建 `app/dropdowns.py` 模块提供 `get_options(key)` 加载函数（启动时加载并缓存）。路由层调用该函数获取选项列表传给模板，替代现有硬编码常量。

**Tech Stack:** Python 3.12, Flask, PyYAML

---

### Task 1: 安装 PyYAML 依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 用 uv 安装 PyYAML**

```bash
cd /home/ubuntu/my-repos/dotTask && uv pip install pyyaml
```

**Step 2: 导出 requirements.txt**

```bash
cd /home/ubuntu/my-repos/dotTask && uv pip freeze > requirements.txt
```

验证 `requirements.txt` 中包含 `pyyaml` 行。

---

### Task 2: 创建 YAML 配置文件

**Files:**
- Create: `config/dropdowns.yaml`

**Step 1: 创建 config 目录和 YAML 文件**

```yaml
# 下拉框选项配置
# 修改后需重启应用生效

location_types:
  - Plant
  - Office
  - Market Office
  - Warehouse
  - R&D Center

statuses:
  - Not Started
  - In Progress
  - Completed
  - On Hold
  - Cancelled

priorities:
  - Critical
  - High
  - Medium
  - Low

local_statuses:
  - Pending
  - In Progress
  - Completed
  - Blocked
  - N/A
```

---

### Task 3: 创建下拉框加载模块

**Files:**
- Create: `app/dropdowns.py`

**Step 1: 编写 app/dropdowns.py**

```python
import os
import yaml

_yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "dropdowns.yaml")
_cache: dict | None = None


def _load():
    global _cache
    with open(_yaml_path, "r", encoding="utf-8") as f:
        _cache = yaml.safe_load(f)


def get_options(key: str) -> list[str]:
    global _cache
    if _cache is None:
        _load()
    return list(_cache.get(key, []))
```

**Step 2: 验证模块可加载**

```bash
cd /home/ubuntu/my-repos/dotTask && .venv/bin/python -c "from app.dropdowns import get_options; print(get_options('location_types'))"
```

预期输出: `['Plant', 'Office', 'Market Office', 'Warehouse', 'R&D Center']`

---

### Task 4: 改造 tasks.py 路由

**Files:**
- Modify: `app/routes/tasks.py`

**Step 1: 替换硬编码常量为 dropdowns 调用**

删除第 10-12 行的三个常量：
```python
STATUS_OPTIONS = ["Not Started", "In Progress", "Completed", "On Hold", "Cancelled"]
PRIORITY_OPTIONS = ["Critical", "High", "Medium", "Low"]
LOCAL_STATUS_OPTIONS = ["Pending", "In Progress", "Completed", "Blocked", "N/A"]
```

添加导入：
```python
from app.dropdowns import get_options
```

**Step 2: 替换所有常量引用**

全文替换映射：
- `STATUS_OPTIONS` → `get_options("statuses")`
- `PRIORITY_OPTIONS` → `get_options("priorities")`
- `LOCAL_STATUS_OPTIONS` → `get_options("local_statuses")`

涉及位置（共 7 处）：
- `list()` 第 42 行: `status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS`
- `create()` 第 82 行: `status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS`
- `create()` 第 83 行: `countries=get_distinct_countries(), location_types=get_distinct_location_types()` → `location_types=get_options("location_types")`
- `detail()` 第 101 行: `status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS`
- `detail()` 第 102 行: `local_status_options=LOCAL_STATUS_OPTIONS`
- `edit()` 第 131 行: `status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS`
- `edit()` 第 132 行: `countries=get_distinct_countries(), location_types=get_distinct_location_types()` → `location_types=get_options("location_types")`
- `update_status()` 第 149 行: `if new_status in STATUS_OPTIONS`

**Step 3: 移除 scope_engine 中 get_distinct_location_types 的导入**

第 6 行改为：
```python
from app.services.scope_engine import get_scope_preview, get_distinct_countries
```

---

### Task 5: 改造 locations.py 路由

**Files:**
- Modify: `app/routes/locations.py`

**Step 1: 添加 dropdowns 导入和传递 location_types 到模板**

在 `locations.py` 顶部添加：
```python
from app.dropdowns import get_options
```

在 `create()` 函数的 `render_template` 调用中添加 `location_types=get_options("location_types")`：
- 第 53 行: `return render_template("locations/form.html", location=None, location_types=get_options("location_types"))`
- 第 72 行: `return render_template("locations/form.html", location=loc, location_types=get_options("location_types"))`

---

### Task 6: 改造 location 表单模板

**Files:**
- Modify: `app/templates/locations/form.html`

**Step 1: 将 location_type 的 `<input>` 改为 `<select>`**

将第 40-44 行：
```html
<!-- Location Type -->
<div>
    <label for="location_type" class="block text-sm font-medium text-gray-700 mb-1">Location Type</label>
    <input type="text" id="location_type" name="location_type" value="{{ location.location_type if location else '' }}" placeholder="Plant / Office / Market Office"
        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
</div>
```

替换为：
```html
<!-- Location Type -->
<div>
    <label for="location_type" class="block text-sm font-medium text-gray-700 mb-1">Location Type</label>
    <select id="location_type" name="location_type"
        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
        <option value="">-- Select Type --</option>
        {% for t in location_types %}
        <option value="{{ t }}" {% if location and location.location_type == t %}selected{% endif %}>{{ t }}</option>
        {% endfor %}
    </select>
</div>
```

---

### Task 7: 改造 scope_engine.py

**Files:**
- Modify: `app/services/scope_engine.py`

**Step 1: 修改 get_distinct_location_types 为从 YAML 读取**

将 `get_distinct_location_types()` 函数替换为：
```python
from app.dropdowns import get_options

def get_distinct_location_types():
    return get_options("location_types")
```

注意：需在文件顶部添加 `from app.dropdowns import get_options`。

---

### Task 8: 验证

**Step 1: 启动应用**

```bash
cd /home/ubuntu/my-repos/dotTask && .venv/bin/python -c "from app import create_app; app = create_app(); print('OK')"
```

预期输出: `OK`

**Step 2: 在浏览器中验证**

- 访问 `/locations/new`：确认 Location Type 是下拉框
- 访问 `/tasks/new`：确认 Status、Priority、Location Type 下拉框正常工作
- 创建一个 location，确认能保存
- 编辑该 location，确认下拉框能回显已选值
