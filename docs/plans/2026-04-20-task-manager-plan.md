# APAC Infra Task Manager 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 APAC_Infra_Task_List.xlsx 转为 Flask + SQLite Web 应用，支持任务创建/分配/跟踪/图表/导入导出。

**Architecture:** Flask 单体应用，SQLAlchemy ORM 操作 SQLite，HTMX 实现无刷新交互，Chart.js 图表，Tailwind CSS 样式。范围引擎根据规则自动将任务分配到匹配地点。

**Tech Stack:** Python 3.12, Flask, Flask-SQLAlchemy, Flask-WTF, WTForms, openpyxl, HTMX, Tailwind CSS (CDN), Chart.js (CDN)

---

### Task 1: 项目脚手架与依赖

**Files:**
- Create: `config.py`
- Create: `run.py`
- Create: `requirements.txt`
- Create: `app/__init__.py`

**Step 1: 安装依赖**

Run: `uv pip install flask flask-sqlalchemy flask-wtf wtforms openpyxl`

**Step 2: 创建 requirements.txt**

```
flask==3.1.0
flask-sqlalchemy==3.1.1
flask-wtf==1.2.2
wtforms==3.2.1
openpyxl==3.1.5
```

Run: `uv pip freeze | grep -iE "flask|sqlalchemy|wtforms|openpyxl" > requirements.txt`

**Step 3: 创建 config.py**

```python
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'tasks.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

**Step 4: 创建 app/__init__.py**

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from . import models
        db.create_all()

    from .routes import dashboard, tasks, locations, data_io
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(locations.bp)
    app.register_blueprint(data_io.bp)

    return app
```

**Step 5: 创建 app/routes/__init__.py 和 app/services/__init__.py**

```python
# app/routes/__init__.py — 空文件
```

```python
# app/services/__init__.py — 空文件
```

**Step 6: 创建 run.py**

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

**Step 7: 创建目录结构**

```bash
mkdir -p app/routes app/services app/templates app/static/css app/static/js instance
```

**Step 8: 验证应用能启动**

Run: `.venv/bin/python -c "from app import create_app; app = create_app(); print('OK')"`

Expected: `OK`

**Step 9: 提交**

```bash
git add config.py run.py requirements.txt app/__init__.py app/routes/__init__.py app/services/__init__.py
git commit -m "feat: project scaffold with Flask + SQLAlchemy"
```

---

### Task 2: 数据模型

**Files:**
- Create: `app/models.py`

**Step 1: 编写模型文件**

```python
from datetime import datetime, timezone
from app import db


class Location(db.Model):
    __tablename__ = "location_master"

    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    location_type = db.Column(db.String(50))
    region = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    it_manager = db.Column(db.String(200))
    primary_it_contact = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    assignments = db.relationship("TaskAssignment", backref="location", lazy="dynamic")

    def __repr__(self):
        return f"<Location {self.location_name}>"


class Task(db.Model):
    __tablename__ = "task_master"

    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(300), nullable=False)
    task_source = db.Column(db.String(200))
    stakeholder = db.Column(db.String(200))
    task_description = db.Column(db.Text)
    scope_type = db.Column(db.String(50), default="Manual")
    scope_rule = db.Column(db.String(300))
    scope_detail = db.Column(db.String(300))
    task_owner = db.Column(db.String(200))
    execution_model = db.Column(db.String(200))
    overall_status = db.Column(db.String(50), default="Not Started")
    start_date = db.Column(db.Date)
    target_date = db.Column(db.Date)
    last_update = db.Column(db.Date)
    link_to_file = db.Column(db.String(500))
    link_to_mail = db.Column(db.String(500))
    task_priority = db.Column(db.String(50), default="Medium")
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    assignments = db.relationship("TaskAssignment", backref="task", lazy="dynamic",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task {self.task_name}>"


class TaskAssignment(db.Model):
    __tablename__ = "task_assignment"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task_master.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location_master.id"), nullable=False)
    it_name = db.Column(db.String(200))
    it_role = db.Column(db.String(200))
    local_responsibility = db.Column(db.String(500))
    local_status = db.Column(db.String(50), default="Pending")
    last_update = db.Column(db.Date)
    issue_blocker = db.Column(db.Text)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("task_id", "location_id", name="uq_task_location"),
    )

    def __repr__(self):
        return f"<Assignment task={self.task_id} loc={self.location_id}>"
```

**Step 2: 验证数据库创建**

Run:
```bash
.venv/bin/python -c "
from app import create_app, db
from app.models import Location, Task, TaskAssignment
app = create_app()
with app.app_context():
    db.create_all()
    print(f'Tables: {db.engine.table_names()}')
"
```

Expected: `Tables: ['location_master', 'task_master', 'task_assignment']`

**Step 3: 提交**

```bash
git add app/models.py
git commit -m "feat: add Location, Task, TaskAssignment models"
```

---

### Task 3: 基础模板与静态资源

**Files:**
- Create: `app/templates/base.html`
- Create: `app/static/css/main.css`

**Step 1: 创建 base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}APAC Infra Task Manager{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex">
                    <div class="flex-shrink-0 flex items-center">
                        <a href="/" class="text-xl font-bold text-gray-800">APAC Task Manager</a>
                    </div>
                    <div class="hidden sm:ml-8 sm:flex sm:space-x-4">
                        <a href="/" class="nav-link {% if request.path == '/' %}text-blue-600 border-b-2 border-blue-600{% else %}text-gray-600{% endif %} inline-flex items-center px-1 pt-1 text-sm font-medium hover:text-blue-600">仪表盘</a>
                        <a href="/tasks" class="nav-link {% if '/task' in request.path %}text-blue-600 border-b-2 border-blue-600{% else %}text-gray-600{% endif %} inline-flex items-center px-1 pt-1 text-sm font-medium hover:text-blue-600">任务</a>
                        <a href="/locations" class="nav-link {% if '/location' in request.path %}text-blue-600 border-b-2 border-blue-600{% else %}text-gray-600{% endif %} inline-flex items-center px-1 pt-1 text-sm font-medium hover:text-blue-600">地点</a>
                        <a href="/data" class="nav-link {% if '/data' in request.path %}text-blue-600 border-b-2 border-blue-600{% else %}text-gray-600{% endif %} inline-flex items-center px-1 pt-1 text-sm font-medium hover:text-blue-600">导入导出</a>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <!-- 主内容 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        {% for category, message in messages %}
        <div class="mb-4 p-4 rounded-md {{ 'bg-green-50 text-green-800' if category == 'success' else 'bg-red-50 text-red-800' if category == 'error' else 'bg-blue-50 text-blue-800' }}">
            {{ message }}
        </div>
        {% endfor %}
        {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

**Step 2: 创建 main.css**

```css
/* HTMX 指示器 */
.htmx-indicator {
    display: none;
}
.htmx-request .htmx-indicator {
    display: inline-block;
}
.htmx-request.htmx-indicator {
    display: inline-block;
}

/* 表格行 hover */
.table-row-hover:hover {
    background-color: #f9fafb;
}

/* 状态颜色标签 */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
}
.badge-not-started { background-color: #e5e7eb; color: #374151; }
.badge-in-progress { background-color: #dbeafe; color: #1d4ed8; }
.badge-completed { background-color: #d1fae5; color: #065f46; }
.badge-on-hold { background-color: #fef3c7; color: #92400e; }
.badge-cancelled { background-color: #fee2e2; color: #991b1b; }
.badge-pending { background-color: #e5e7eb; color: #374151; }
.badge-blocked { background-color: #fee2e2; color: #991b1b; }
.badge-na { background-color: #f3f4f6; color: #6b7280; }
.badge-critical { background-color: #fee2e2; color: #991b1b; }
.badge-high { background-color: #fef3c7; color: #92400e; }
.badge-medium { background-color: #dbeafe; color: #1d4ed8; }
.badge-low { background-color: #d1fae5; color: #065f46; }
```

**Step 3: 提交**

```bash
git add app/templates/base.html app/static/css/main.css
git commit -m "feat: base template with Tailwind, HTMX, Chart.js CDN"
```

---

### Task 4: 范围引擎（Scope Engine）

**Files:**
- Create: `app/services/scope_engine.py`

**Step 1: 实现范围匹配逻辑**

```python
from app import db
from app.models import Location


def get_matching_locations(scope_type, scope_detail):
    """根据 scope_type 和 scope_detail 返回匹配的活跃地点列表。"""
    query = Location.query.filter_by(is_active=True)

    if scope_type == "All":
        pass
    elif scope_type == "Country":
        if scope_detail:
            query = query.filter_by(country=scope_detail)
    elif scope_type == "Location_Type":
        if scope_detail:
            query = query.filter_by(location_type=scope_detail)
    elif scope_type == "Region":
        if scope_detail:
            query = query.filter_by(region=scope_detail)
    elif scope_type == "Manual":
        return []

    return query.order_by(Location.location_name).all()


def get_scope_preview(scope_type, scope_detail):
    """返回匹配数量和地点名称列表，用于预览。"""
    locations = get_matching_locations(scope_type, scope_detail)
    return {
        "count": len(locations),
        "names": [loc.location_name for loc in locations],
        "locations": locations,
    }
```

**Step 2: 验证**

Run:
```bash
.venv/bin/python -c "
from app import create_app
from app.services.scope_engine import get_scope_preview
app = create_app()
with app.app_context():
    result = get_scope_preview('All', None)
    print(f'All locations (empty db): count={result[\"count\"]}')
    result = get_scope_preview('Manual', None)
    print(f'Manual: count={result[\"count\"]}')
    print('OK')
"
```

Expected:
```
All locations (empty db): count=0
Manual: count=0
OK
```

**Step 3: 提交**

```bash
git add app/services/scope_engine.py
git commit -m "feat: scope engine for rule-based location matching"
```

---

### Task 5: 地点管理 CRUD

**Files:**
- Create: `app/routes/locations.py`
- Create: `app/templates/locations/list.html`
- Create: `app/templates/locations/form.html`

**Step 1: 创建 locations.py 路由**

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Location

bp = Blueprint("locations", __name__, url_prefix="/locations")


@bp.route("/")
def list():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    search = request.args.get("search", "")
    active_filter = request.args.get("active", "")

    query = Location.query
    if search:
        query = query.filter(
            db.or_(
                Location.location_name.ilike(f"%{search}%"),
                Location.country.ilike(f"%{search}%"),
                Location.city.ilike(f"%{search}%"),
            )
        )
    if active_filter == "yes":
        query = query.filter_by(is_active=True)
    elif active_filter == "no":
        query = query.filter_by(is_active=False)

    locations = query.order_by(Location.location_name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template("locations/list.html", locations=locations, search=search, active_filter=active_filter)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        loc = Location(
            location_name=request.form["location_name"],
            country=request.form.get("country", ""),
            city=request.form.get("city", ""),
            location_type=request.form.get("location_type", ""),
            region=request.form.get("region", ""),
            is_active=request.form.get("is_active") == "on",
            it_manager=request.form.get("it_manager", ""),
            primary_it_contact=request.form.get("primary_it_contact", ""),
        )
        db.session.add(loc)
        db.session.commit()
        flash("地点已创建", "success")
        return redirect(url_for("locations.list"))

    return render_template("locations/form.html", location=None)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    loc = Location.query.get_or_404(id)
    if request.method == "POST":
        loc.location_name = request.form["location_name"]
        loc.country = request.form.get("country", "")
        loc.city = request.form.get("city", "")
        loc.location_type = request.form.get("location_type", "")
        loc.region = request.form.get("region", "")
        loc.is_active = request.form.get("is_active") == "on"
        loc.it_manager = request.form.get("it_manager", "")
        loc.primary_it_contact = request.form.get("primary_it_contact", "")
        db.session.commit()
        flash("地点已更新", "success")
        return redirect(url_for("locations.list"))

    return render_template("locations/form.html", location=loc)


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    loc = Location.query.get_or_404(id)
    db.session.delete(loc)
    db.session.commit()
    flash("地点已删除", "success")
    return redirect(url_for("locations.list"))


@bp.route("/<int:id>/toggle-active", methods=["POST"])
def toggle_active(id):
    loc = Location.query.get_or_404(id)
    loc.is_active = not loc.is_active
    db.session.commit()
    status = "激活" if loc.is_active else "停用"
    flash(f"已{status}地点 {loc.location_name}", "success")
    return redirect(url_for("locations.list"))
```

**Step 2: 创建 locations/list.html**

```html
{% extends "base.html" %}

{% block title %}地点管理 - APAC Task Manager{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-gray-900">地点管理</h1>
    <a href="{{ url_for('locations.create') }}" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">新建地点</a>
</div>

<!-- 筛选 -->
<form method="get" class="mb-6 flex gap-4 items-end">
    <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">搜索</label>
        <input type="text" name="search" value="{{ search }}" placeholder="名称/国家/城市" class="border rounded-md px-3 py-2 text-sm w-48">
    </div>
    <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
        <select name="active" class="border rounded-md px-3 py-2 text-sm">
            <option value="">全部</option>
            <option value="yes" {% if active_filter == 'yes' %}selected{% endif %}>活跃</option>
            <option value="no" {% if active_filter == 'no' %}selected{% endif %}>停用</option>
        </select>
    </div>
    <button type="submit" class="bg-gray-600 text-white px-4 py-2 rounded-md text-sm hover:bg-gray-700">筛选</button>
    <a href="{{ url_for('locations.list') }}" class="text-sm text-gray-500 hover:text-gray-700">重置</a>
</form>

<!-- 列表 -->
<div class="bg-white shadow rounded-lg overflow-hidden">
    <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
            <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">地点名称</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">国家</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">城市</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">区域</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
            {% for loc in locations.items %}
            <tr class="table-row-hover">
                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ loc.location_name }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ loc.country or '-' }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ loc.city or '-' }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ loc.location_type or '-' }}</td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ loc.region or '-' }}</td>
                <td class="px-4 py-3 text-sm">
                    {% if loc.is_active %}
                    <span class="badge badge-completed">活跃</span>
                    {% else %}
                    <span class="badge badge-cancelled">停用</span>
                    {% endif %}
                </td>
                <td class="px-4 py-3 text-sm space-x-2">
                    <a href="{{ url_for('locations.edit', id=loc.id) }}" class="text-blue-600 hover:text-blue-800">编辑</a>
                    <form method="POST" action="{{ url_for('locations.toggle_active', id=loc.id) }}" class="inline">
                        <button type="submit" class="text-yellow-600 hover:text-yellow-800">
                            {{ '停用' if loc.is_active else '激活' }}
                        </button>
                    </form>
                    <form method="POST" action="{{ url_for('locations.delete', id=loc.id) }}" class="inline"
                          onsubmit="return confirm('确定删除此地点？')">
                        <button type="submit" class="text-red-600 hover:text-red-800">删除</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
            {% if not locations.items %}
            <tr><td colspan="7" class="px-4 py-8 text-center text-gray-500">暂无地点数据</td></tr>
            {% endif %}
        </tbody>
    </table>
</div>

<!-- 分页 -->
{% if locations.pages > 1 %}
<div class="mt-4 flex justify-center gap-2">
    {% if locations.has_prev %}
    <a href="{{ url_for('locations.list', page=locations.prev_num, search=search, active=active_filter) }}" class="px-3 py-1 border rounded text-sm hover:bg-gray-50">上一页</a>
    {% endif %}
    <span class="px-3 py-1 text-sm text-gray-600">{{ locations.page }} / {{ locations.pages }}</span>
    {% if locations.has_next %}
    <a href="{{ url_for('locations.list', page=locations.next_num, search=search, active=active_filter) }}" class="px-3 py-1 border rounded text-sm hover:bg-gray-50">下一页</a>
    {% endif %}
</div>
{% endif %}
{% endblock %}
```

**Step 3: 创建 locations/form.html**

```html
{% extends "base.html" %}

{% block title %}{{ '编辑地点' if location else '新建地点' }} - APAC Task Manager{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ '编辑地点' if location else '新建地点' }}</h1>

    <form method="POST" class="bg-white shadow rounded-lg p-6 space-y-4">
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">地点名称 *</label>
                <input type="text" name="location_name" value="{{ location.location_name if location else '' }}" required
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">国家</label>
                <input type="text" name="country" value="{{ location.country if location else '' }}"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">城市</label>
                <input type="text" name="city" value="{{ location.city if location else '' }}"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">地点类型</label>
                <input type="text" name="location_type" value="{{ location.location_type if location else '' }}"
                       placeholder="Plant / Office / Market Office 等"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">区域</label>
                <input type="text" name="region" value="{{ location.region if location else '' }}"
                       placeholder="APAC-North / APAC-South 等"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">IT 经理</label>
                <input type="text" name="it_manager" value="{{ location.it_manager if location else '' }}"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">主要 IT 联系人</label>
                <input type="text" name="primary_it_contact" value="{{ location.primary_it_contact if location else '' }}"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div class="flex items-center">
                <label class="flex items-center gap-2 text-sm">
                    <input type="checkbox" name="is_active" {% if not location or location.is_active %}checked{% endif %}
                           class="rounded border-gray-300">
                    活跃
                </label>
            </div>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t">
            <a href="{{ url_for('locations.list') }}" class="px-4 py-2 border rounded-md text-sm text-gray-600 hover:bg-gray-50">取消</a>
            <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700">保存</button>
        </div>
    </form>
</div>
{% endblock %}
```

**Step 4: 提交**

```bash
git add app/routes/locations.py app/templates/locations/
git commit -m "feat: location CRUD with search, filter, pagination"
```

---

### Task 6: 任务 CRUD

**Files:**
- Create: `app/routes/tasks.py`
- Create: `app/templates/tasks/list.html`
- Create: `app/templates/tasks/form.html`
- Create: `app/templates/tasks/detail.html`

**Step 1: 创建 tasks.py 路由**

```python
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Task, TaskAssignment, Location
from app.services.scope_engine import get_matching_locations, get_scope_preview

bp = Blueprint("tasks", __name__, url_prefix="/tasks")

STATUS_OPTIONS = ["Not Started", "In Progress", "Completed", "On Hold", "Cancelled"]
PRIORITY_OPTIONS = ["Critical", "High", "Medium", "Low"]
SCOPE_TYPES = ["All", "Country", "Location_Type", "Region", "Manual"]
LOCAL_STATUS_OPTIONS = ["Pending", "In Progress", "Completed", "Blocked", "N/A"]


@bp.route("/")
def list():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    search = request.args.get("search", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")

    query = Task.query
    if search:
        query = query.filter(
            db.or_(
                Task.task_name.ilike(f"%{search}%"),
                Task.task_description.ilike(f"%{search}%"),
            )
        )
    if status:
        query = query.filter_by(overall_status=status)
    if priority:
        query = query.filter_by(task_priority=priority)

    tasks = query.order_by(Task.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template(
        "tasks/list.html",
        tasks=tasks, search=search, status=status, priority=priority,
        status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS,
    )


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        task = Task(
            task_name=request.form["task_name"],
            task_source=request.form.get("task_source", ""),
            stakeholder=request.form.get("stakeholder", ""),
            task_description=request.form.get("task_description", ""),
            scope_type=request.form.get("scope_type", "Manual"),
            scope_rule=request.form.get("scope_rule", ""),
            scope_detail=request.form.get("scope_detail", ""),
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

        # 自动分配
        if task.scope_type != "Manual":
            locations = get_matching_locations(task.scope_type, task.scope_detail)
            for loc in locations:
                assignment = TaskAssignment(task_id=task.id, location_id=loc.id)
                db.session.add(assignment)

        db.session.commit()
        flash("任务已创建", "success")
        return redirect(url_for("tasks.detail", id=task.id))

    return render_template(
        "tasks/form.html", task=None,
        status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS,
        scope_types=SCOPE_TYPES, locations=Location.query.filter_by(is_active=True).order_by(Location.location_name).all(),
    )


@bp.route("/<int:id>")
def detail(id):
    task = Task.query.get_or_404(id)
    assignments = task.assignments.order_by(TaskAssignment.id).all()
    assigned_location_ids = [a.location_id for a in assignments]
    unassigned_locations = (
        Location.query.filter_by(is_active=True)
        .filter(~Location.id.in_(assigned_location_ids))
        .order_by(Location.location_name).all()
    ) if assigned_location_ids else Location.query.filter_by(is_active=True).order_by(Location.location_name).all()

    return render_template(
        "tasks/detail.html", task=task, assignments=assignments,
        unassigned_locations=unassigned_locations,
        status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS,
        local_status_options=LOCAL_STATUS_OPTIONS, scope_types=SCOPE_TYPES,
    )


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    task = Task.query.get_or_404(id)
    if request.method == "POST":
        task.task_name = request.form["task_name"]
        task.task_source = request.form.get("task_source", "")
        task.stakeholder = request.form.get("stakeholder", "")
        task.task_description = request.form.get("task_description", "")
        task.scope_type = request.form.get("scope_type", "Manual")
        task.scope_rule = request.form.get("scope_rule", "")
        task.scope_detail = request.form.get("scope_detail", "")
        task.task_owner = request.form.get("task_owner", "")
        task.execution_model = request.form.get("execution_model", "")
        task.overall_status = request.form.get("overall_status", "Not Started")
        task.start_date = _parse_date(request.form.get("start_date"))
        task.target_date = _parse_date(request.form.get("target_date"))
        task.last_update = date.today()
        task.link_to_file = request.form.get("link_to_file", "")
        task.link_to_mail = request.form.get("link_to_mail", "")
        task.task_priority = request.form.get("task_priority", "Medium")
        task.comments = request.form.get("comments", "")
        db.session.commit()
        flash("任务已更新", "success")
        return redirect(url_for("tasks.detail", id=task.id))

    return render_template(
        "tasks/form.html", task=task,
        status_options=STATUS_OPTIONS, priority_options=PRIORITY_OPTIONS,
        scope_types=SCOPE_TYPES, locations=Location.query.filter_by(is_active=True).order_by(Location.location_name).all(),
    )


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash("任务已删除", "success")
    return redirect(url_for("tasks.list"))


@bp.route("/<int:id>/status", methods=["POST"])
def update_status(id):
    """HTMX: 行内快速更新状态"""
    task = Task.query.get_or_404(id)
    new_status = request.form.get("overall_status")
    if new_status in STATUS_OPTIONS:
        task.overall_status = new_status
        task.last_update = date.today()
        db.session.commit()
    return redirect(request.headers.get("Referer", url_for("tasks.list")))


@bp.route("/<int:id>/assign", methods=["POST"])
def assign_location(id):
    """手动添加地点分配"""
    task = Task.query.get_or_404(id)
    location_id = request.form.get("location_id", type=int)
    if location_id:
        existing = TaskAssignment.query.filter_by(task_id=id, location_id=location_id).first()
        if not existing:
            assignment = TaskAssignment(
                task_id=id,
                location_id=location_id,
                it_name=request.form.get("it_name", ""),
                it_role=request.form.get("it_role", ""),
                local_responsibility=request.form.get("local_responsibility", ""),
            )
            db.session.add(assignment)
            db.session.commit()
            flash("已分配地点", "success")
    return redirect(url_for("tasks.detail", id=id))


@bp.route("/<int:task_id>/assignment/<int:assignment_id>", methods=["POST"])
def update_assignment(task_id, assignment_id):
    """更新分配的本地状态"""
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    assignment.local_status = request.form.get("local_status", assignment.local_status)
    assignment.issue_blocker = request.form.get("issue_blocker", assignment.issue_blocker or "")
    assignment.comments = request.form.get("comments", assignment.comments or "")
    assignment.it_name = request.form.get("it_name", assignment.it_name or "")
    assignment.last_update = date.today()
    db.session.commit()
    flash("分配状态已更新", "success")
    return redirect(url_for("tasks.detail", id=task_id))


@bp.route("/<int:task_id>/assignment/<int:assignment_id>/delete", methods=["POST"])
def remove_assignment(task_id, assignment_id):
    """移除分配"""
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash("已移除分配", "success")
    return redirect(url_for("tasks.detail", id=task_id))


@bp.route("/scope-preview", methods=["POST"])
def scope_preview():
    """AJAX: 预览范围匹配的地点"""
    scope_type = request.form.get("scope_type", "Manual")
    scope_detail = request.form.get("scope_detail", "")
    preview = get_scope_preview(scope_type, scope_detail)
    return jsonify(preview)


def _parse_date(value):
    if value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None
```

**Step 2: 创建 tasks/list.html**

```html
{% extends "base.html" %}

{% block title %}任务列表 - APAC Task Manager{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-gray-900">任务列表</h1>
    <a href="{{ url_for('tasks.create') }}" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">新建任务</a>
</div>

<!-- 筛选 -->
<form method="get" class="mb-6 flex gap-4 items-end flex-wrap">
    <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">搜索</label>
        <input type="text" name="search" value="{{ search }}" placeholder="任务名/描述" class="border rounded-md px-3 py-2 text-sm w-48">
    </div>
    <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
        <select name="status" class="border rounded-md px-3 py-2 text-sm">
            <option value="">全部</option>
            {% for s in status_options %}
            <option value="{{ s }}" {% if status == s %}selected{% endif %}>{{ s }}</option>
            {% endfor %}
        </select>
    </div>
    <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">优先级</label>
        <select name="priority" class="border rounded-md px-3 py-2 text-sm">
            <option value="">全部</option>
            {% for p in priority_options %}
            <option value="{{ p }}" {% if priority == p %}selected{% endif %}>{{ p }}</option>
            {% endfor %}
        </select>
    </div>
    <button type="submit" class="bg-gray-600 text-white px-4 py-2 rounded-md text-sm hover:bg-gray-700">筛选</button>
    <a href="{{ url_for('tasks.list') }}" class="text-sm text-gray-500 hover:text-gray-700">重置</a>
</form>

<!-- 列表 -->
<div class="bg-white shadow rounded-lg overflow-hidden">
    <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
            <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">任务名称</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">优先级</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">负责人</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">目标日期</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">范围</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
            {% for task in tasks.items %}
            <tr class="table-row-hover">
                <td class="px-4 py-3">
                    <a href="{{ url_for('tasks.detail', id=task.id) }}" class="text-sm font-medium text-blue-600 hover:text-blue-800">{{ task.task_name }}</a>
                </td>
                <td class="px-4 py-3">
                    <span class="badge badge-{{ task.task_priority|lower }}">{{ task.task_priority }}</span>
                </td>
                <td class="px-4 py-3">
                    <form method="POST" action="{{ url_for('tasks.update_status', id=task.id) }}" class="inline">
                        <select name="overall_status" onchange="this.form.submit()"
                                class="text-xs border rounded px-2 py-1">
                            {% for s in status_options %}
                            <option value="{{ s }}" {% if task.overall_status == s %}selected{% endif %}>{{ s }}</option>
                            {% endfor %}
                        </select>
                    </form>
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ task.task_owner or '-' }}</td>
                <td class="px-4 py-3 text-sm text-gray-600 {{ 'text-red-600 font-semibold' if task.target_date and task.target_date < today and task.overall_status not in ['Completed', 'Cancelled'] }}">
                    {{ task.target_date or '-' }}
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">{{ task.scope_type }}</td>
                <td class="px-4 py-3 text-sm space-x-2">
                    <a href="{{ url_for('tasks.detail', id=task.id) }}" class="text-blue-600 hover:text-blue-800">详情</a>
                    <a href="{{ url_for('tasks.edit', id=task.id) }}" class="text-blue-600 hover:text-blue-800">编辑</a>
                    <form method="POST" action="{{ url_for('tasks.delete', id=task.id) }}" class="inline"
                          onsubmit="return confirm('确定删除此任务？')">
                        <button type="submit" class="text-red-600 hover:text-red-800">删除</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
            {% if not tasks.items %}
            <tr><td colspan="7" class="px-4 py-8 text-center text-gray-500">暂无任务</td></tr>
            {% endif %}
        </tbody>
    </table>
</div>

<!-- 分页 -->
{% if tasks.pages > 1 %}
<div class="mt-4 flex justify-center gap-2">
    {% if tasks.has_prev %}
    <a href="{{ url_for('tasks.list', page=tasks.prev_num, search=search, status=status, priority=priority) }}" class="px-3 py-1 border rounded text-sm hover:bg-gray-50">上一页</a>
    {% endif %}
    <span class="px-3 py-1 text-sm text-gray-600">{{ tasks.page }} / {{ tasks.pages }}</span>
    {% if tasks.has_next %}
    <a href="{{ url_for('tasks.list', page=tasks.next_num, search=search, status=status, priority=priority) }}" class="px-3 py-1 border rounded text-sm hover:bg-gray-50">下一页</a>
    {% endif %}
</div>
{% endif %}
{% endblock %}
```

**Step 3: 创建 tasks/form.html**

```html
{% extends "base.html" %}

{% block title %}{{ '编辑任务' if task else '新建任务' }} - APAC Task Manager{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ '编辑任务' if task else '新建任务' }}</h1>

    <form method="POST" id="task-form" class="bg-white shadow rounded-lg p-6 space-y-6">
        <!-- 基本信息 -->
        <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">任务名称 *</label>
                <input type="text" name="task_name" value="{{ task.task_name if task else '' }}" required
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">来源</label>
                <input type="text" name="task_source" value="{{ task.task_source if task else '' }}"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">干系人</label>
                <input type="text" name="stakeholder" value="{{ task.stakeholder if task else '' }}"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">负责人</label>
                <input type="text" name="task_owner" value="{{ task.task_owner if task else '' }}"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">执行模式</label>
                <input type="text" name="execution_model" value="{{ task.execution_model if task else '' }}"
                       class="w-full border rounded-md px-3 py-2 text-sm">
            </div>
            <div class="col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea name="task_description" rows="3" class="w-full border rounded-md px-3 py-2 text-sm">{{ task.task_description if task else '' }}</textarea>
            </div>
        </div>

        <!-- 范围 -->
        <div class="border-t pt-4">
            <h3 class="text-sm font-semibold text-gray-700 mb-3">分配范围</h3>
            <div class="grid grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">范围类型</label>
                    <select name="scope_type" id="scope_type" class="w-full border rounded-md px-3 py-2 text-sm">
                        {% for st in scope_types %}
                        <option value="{{ st }}" {% if task and task.scope_type == st %}selected{% endif %}>{{ st }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">规则说明</label>
                    <input type="text" name="scope_rule" value="{{ task.scope_rule if task else '' }}"
                           class="w-full border rounded-md px-3 py-2 text-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">规则值</label>
                    <input type="text" name="scope_detail" id="scope_detail" value="{{ task.scope_detail if task else '' }}"
                           placeholder="如 China / Plant / APAC-North"
                           class="w-full border rounded-md px-3 py-2 text-sm">
                </div>
            </div>
            <div id="scope-preview" class="mt-2 text-sm text-gray-500"></div>
        </div>

        <!-- 状态与日期 -->
        <div class="border-t pt-4">
            <h3 class="text-sm font-semibold text-gray-700 mb-3">状态与日期</h3>
            <div class="grid grid-cols-4 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
                    <select name="overall_status" class="w-full border rounded-md px-3 py-2 text-sm">
                        {% for s in status_options %}
                        <option value="{{ s }}" {% if task and task.overall_status == s %}selected{% endif %}>{{ s }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">优先级</label>
                    <select name="task_priority" class="w-full border rounded-md px-3 py-2 text-sm">
                        {% for p in priority_options %}
                        <option value="{{ p }}" {% if task and task.task_priority == p %}selected{% endif %}>{{ p }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">开始日期</label>
                    <input type="date" name="start_date" value="{{ task.start_date if task else '' }}"
                           class="w-full border rounded-md px-3 py-2 text-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">目标日期</label>
                    <input type="date" name="target_date" value="{{ task.target_date if task else '' }}"
                           class="w-full border rounded-md px-3 py-2 text-sm">
                </div>
            </div>
        </div>

        <!-- 链接与备注 -->
        <div class="border-t pt-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">文件链接</label>
                    <input type="text" name="link_to_file" value="{{ task.link_to_file if task else '' }}"
                           class="w-full border rounded-md px-3 py-2 text-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">邮件链接</label>
                    <input type="text" name="link_to_mail" value="{{ task.link_to_mail if task else '' }}"
                           class="w-full border rounded-md px-3 py-2 text-sm">
                </div>
                <div class="col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">备注</label>
                    <textarea name="comments" rows="2" class="w-full border rounded-md px-3 py-2 text-sm">{{ task.comments if task else '' }}</textarea>
                </div>
            </div>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t">
            <a href="{{ url_for('tasks.list') }}" class="px-4 py-2 border rounded-md text-sm text-gray-600 hover:bg-gray-50">取消</a>
            <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700">保存</button>
        </div>
    </form>
</div>

<script>
document.getElementById('scope_type').addEventListener('change', previewScope);
document.getElementById('scope_detail').addEventListener('input', previewScope);

function previewScope() {
    const scopeType = document.getElementById('scope_type').value;
    const scopeDetail = document.getElementById('scope_detail').value;
    if (scopeType === 'Manual') {
        document.getElementById('scope-preview').textContent = '手动分配 — 保存后在详情页手动选择地点';
        return;
    }
    fetch('/tasks/scope-preview', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `scope_type=${encodeURIComponent(scopeType)}&scope_detail=${encodeURIComponent(scopeDetail)}`
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('scope-preview').textContent = `将分配给 ${data.count} 个地点：${data.names.join(', ') || '无匹配'}`;
    });
}
</script>
{% endblock %}
```

**Step 4: 创建 tasks/detail.html**

```html
{% extends "base.html" %}

{% block title %}{{ task.task_name }} - APAC Task Manager{% endblock %}

{% block content %}
<div class="max-w-6xl mx-auto">
    <!-- 头部 -->
    <div class="flex justify-between items-start mb-6">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ task.task_name }}</h1>
            <div class="mt-2 flex gap-2">
                <span class="badge badge-{{ task.overall_status|lower|replace(' ', '-') }}">{{ task.overall_status }}</span>
                <span class="badge badge-{{ task.task_priority|lower }}">{{ task.task_priority }}</span>
                <span class="text-sm text-gray-500">范围: {{ task.scope_type }}{% if task.scope_detail %} ({{ task.scope_detail }}){% endif %}</span>
            </div>
        </div>
        <div class="flex gap-2">
            <a href="{{ url_for('tasks.edit', id=task.id) }}" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">编辑</a>
            <form method="POST" action="{{ url_for('tasks.delete', id=task.id) }}" onsubmit="return confirm('确定删除？')">
                <button type="submit" class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm">删除</button>
            </form>
        </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
        <!-- 左侧：任务信息 -->
        <div class="col-span-2 space-y-6">
            <!-- 基本信息 -->
            <div class="bg-white shadow rounded-lg p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>
                <dl class="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                    <div><dt class="text-gray-500">来源</dt><dd class="text-gray-900">{{ task.task_source or '-' }}</dd></div>
                    <div><dt class="text-gray-500">干系人</dt><dd class="text-gray-900">{{ task.stakeholder or '-' }}</dd></div>
                    <div><dt class="text-gray-500">负责人</dt><dd class="text-gray-900">{{ task.task_owner or '-' }}</dd></div>
                    <div><dt class="text-gray-500">执行模式</dt><dd class="text-gray-900">{{ task.execution_model or '-' }}</dd></div>
                    <div><dt class="text-gray-500">开始日期</dt><dd class="text-gray-900">{{ task.start_date or '-' }}</dd></div>
                    <div><dt class="text-gray-500">目标日期</dt><dd class="text-gray-900">{{ task.target_date or '-' }}</dd></div>
                    <div class="col-span-2"><dt class="text-gray-500">描述</dt><dd class="text-gray-900 whitespace-pre-wrap">{{ task.task_description or '-' }}</dd></div>
                    {% if task.link_to_file %}
                    <div class="col-span-2"><dt class="text-gray-500">文件链接</dt><dd><a href="{{ task.link_to_file }}" class="text-blue-600 hover:underline" target="_blank">{{ task.link_to_file }}</a></dd></div>
                    {% endif %}
                    {% if task.comments %}
                    <div class="col-span-2"><dt class="text-gray-500">备注</dt><dd class="text-gray-900 whitespace-pre-wrap">{{ task.comments }}</dd></div>
                    {% endif %}
                </dl>
            </div>

            <!-- 地点分配列表 -->
            <div class="bg-white shadow rounded-lg p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">地点分配 ({{ assignments|length }})</h2>
                {% if assignments %}
                <div class="space-y-3">
                    {% for a in assignments %}
                    <div class="border rounded-lg p-4">
                        <form method="POST" action="{{ url_for('tasks.update_assignment', task_id=task.id, assignment_id=a.id) }}">
                            <div class="flex justify-between items-start">
                                <div>
                                    <span class="font-medium text-sm">{{ a.location.location_name }}</span>
                                    <span class="text-gray-400 text-xs ml-2">{{ a.location.country or '' }} / {{ a.location.city or '' }}</span>
                                </div>
                                <div class="flex gap-2 items-center">
                                    <select name="local_status" class="text-xs border rounded px-2 py-1">
                                        {% for ls in local_status_options %}
                                        <option value="{{ ls }}" {% if a.local_status == ls %}selected{% endif %}>{{ ls }}</option>
                                        {% endfor %}
                                    </select>
                                    <button type="submit" class="text-xs bg-gray-100 px-2 py-1 rounded hover:bg-gray-200">更新</button>
                                    <form method="POST" action="{{ url_for('tasks.remove_assignment', task_id=task.id, assignment_id=a.id) }}"
                                          onsubmit="return confirm('确定移除此分配？')" class="inline">
                                        <button type="submit" class="text-xs text-red-600 hover:text-red-800">移除</button>
                                    </form>
                                </div>
                            </div>
                            <div class="grid grid-cols-3 gap-2 mt-2 text-xs">
                                <div>
                                    <label class="text-gray-500">IT 人员</label>
                                    <input type="text" name="it_name" value="{{ a.it_name or '' }}" class="w-full border rounded px-2 py-1">
                                </div>
                                <div>
                                    <label class="text-gray-500">阻碍项</label>
                                    <input type="text" name="issue_blocker" value="{{ a.issue_blocker or '' }}" class="w-full border rounded px-2 py-1">
                                </div>
                                <div>
                                    <label class="text-gray-500">备注</label>
                                    <input type="text" name="comments" value="{{ a.comments or '' }}" class="w-full border rounded px-2 py-1">
                                </div>
                            </div>
                        </form>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <p class="text-gray-500 text-sm">暂无分配</p>
                {% endif %}

                <!-- 添加分配 -->
                {% if unassigned_locations %}
                <div class="mt-4 pt-4 border-t">
                    <h3 class="text-sm font-medium text-gray-700 mb-2">添加地点</h3>
                    <form method="POST" action="{{ url_for('tasks.assign_location', id=task.id) }}" class="flex gap-2 items-end">
                        <select name="location_id" class="border rounded-md px-3 py-2 text-sm flex-1">
                            {% for loc in unassigned_locations %}
                            <option value="{{ loc.id }}">{{ loc.location_name }} ({{ loc.country or '' }})</option>
                            {% endfor %}
                        </select>
                        <button type="submit" class="bg-green-600 text-white px-4 py-2 rounded-md text-sm hover:bg-green-700">分配</button>
                    </form>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- 右侧：概要 -->
        <div class="space-y-6">
            <div class="bg-white shadow rounded-lg p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">进度概要</h2>
                <div class="space-y-3 text-sm">
                    <div class="flex justify-between">
                        <span class="text-gray-500">总分配</span>
                        <span class="font-medium">{{ assignments|length }}</span>
                    </div>
                    {% for status in local_status_options %}
                    {% set count = assignments|selectattr('local_status', 'equalto', status)|list|length %}
                    {% if count > 0 %}
                    <div class="flex justify-between">
                        <span class="text-gray-500">{{ status }}</span>
                        <span class="font-medium">{{ count }}</span>
                    </div>
                    {% endif %}
                    {% endfor %}
                    {% set blocked = assignments|selectattr('local_status', 'equalto', 'Blocked')|list %}
                    {% if blocked %}
                    <div class="mt-4 p-3 bg-red-50 rounded">
                        <h3 class="font-medium text-red-800 text-xs mb-1">阻塞项</h3>
                        {% for b in blocked %}
                        <p class="text-xs text-red-700">{{ b.location.location_name }}: {{ b.issue_blocker or '无详情' }}</p>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 5: 提交**

```bash
git add app/routes/tasks.py app/templates/tasks/
git commit -m "feat: task CRUD with scope engine, assignment management, detail page"
```

---

### Task 7: 仪表盘

**Files:**
- Create: `app/routes/dashboard.py`
- Create: `app/templates/dashboard/index.html`
- Create: `app/static/js/dashboard.js`

**Step 1: 创建 dashboard.py**

```python
from datetime import date, timedelta
from flask import Blueprint, render_template
from app import db
from app.models import Task, TaskAssignment, Location

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    today = date.today()
    week_later = today + timedelta(days=7)

    total_tasks = Task.query.count()
    in_progress = Task.query.filter_by(overall_status="In Progress").count()
    completed = Task.query.filter_by(overall_status="Completed").count()
    on_hold = Task.query.filter_by(overall_status="On Hold").count()

    overdue = Task.query.filter(
        Task.target_date < today,
        Task.overall_status.notin_(["Completed", "Cancelled"]),
    ).count()

    blocked = TaskAssignment.query.filter_by(local_status="Blocked").count()

    overdue_tasks = Task.query.filter(
        Task.target_date < today,
        Task.overall_status.notin_(["Completed", "Cancelled"]),
    ).order_by(Task.target_date).limit(10).all()

    upcoming_tasks = Task.query.filter(
        Task.target_date.between(today, week_later),
        Task.overall_status.notin_(["Completed", "Cancelled"]),
    ).order_by(Task.target_date).all()

    # 图表数据
    status_data = db.session.query(Task.overall_status, db.func.count(Task.id)).group_by(Task.overall_status).all()
    priority_data = db.session.query(Task.task_priority, db.func.count(Task.id)).group_by(Task.task_priority).all()

    # 按地点统计
    location_stats = (
        db.session.query(
            Location.location_name,
            db.func.count(TaskAssignment.id).label("total"),
            db.func.sum(db.case((TaskAssignment.local_status == "Completed", 1), else_=0)).label("done"),
        )
        .join(TaskAssignment, TaskAssignment.location_id == Location.id)
        .group_by(Location.id)
        .order_by(db.desc(db.func.count(TaskAssignment.id)))
        .limit(10)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        total_tasks=total_tasks, in_progress=in_progress,
        completed=completed, on_hold=on_hold,
        overdue=overdue, blocked=blocked,
        overdue_tasks=overdue_tasks, upcoming_tasks=upcoming_tasks,
        status_data=dict(status_data), priority_data=dict(priority_data),
        location_stats=location_stats, today=today,
    )
```

**Step 2: 创建 dashboard/index.html**

```html
{% extends "base.html" %}

{% block title %}仪表盘 - APAC Task Manager{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-gray-900">仪表盘</h1>
    <button onclick="exportPDF()" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 text-sm">导出 PDF 报告</button>
</div>

<!-- 统计卡片 -->
<div class="grid grid-cols-5 gap-4 mb-8">
    <div class="bg-white shadow rounded-lg p-4">
        <div class="text-2xl font-bold text-gray-900">{{ total_tasks }}</div>
        <div class="text-sm text-gray-500">总任务</div>
    </div>
    <div class="bg-white shadow rounded-lg p-4">
        <div class="text-2xl font-bold text-blue-600">{{ in_progress }}</div>
        <div class="text-sm text-gray-500">进行中</div>
    </div>
    <div class="bg-white shadow rounded-lg p-4">
        <div class="text-2xl font-bold text-green-600">{{ completed }}</div>
        <div class="text-sm text-gray-500">已完成</div>
    </div>
    <div class="bg-white shadow rounded-lg p-4">
        <div class="text-2xl font-bold text-red-600">{{ overdue }}</div>
        <div class="text-sm text-gray-500">逾期</div>
    </div>
    <div class="bg-white shadow rounded-lg p-4">
        <div class="text-2xl font-bold text-orange-600">{{ blocked }}</div>
        <div class="text-sm text-gray-500">有阻塞</div>
    </div>
</div>

<!-- 图表 -->
<div class="grid grid-cols-2 gap-6 mb-8">
    <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-sm font-semibold text-gray-700 mb-4">任务状态分布</h3>
        <canvas id="statusChart"></canvas>
    </div>
    <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-sm font-semibold text-gray-700 mb-4">优先级分布</h3>
        <canvas id="priorityChart"></canvas>
    </div>
    <div class="bg-white shadow rounded-lg p-6 col-span-2">
        <h3 class="text-sm font-semibold text-gray-700 mb-4">各地点进度</h3>
        <canvas id="locationChart"></canvas>
    </div>
</div>

<!-- 提醒 -->
<div class="grid grid-cols-2 gap-6">
    {% if overdue_tasks %}
    <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-sm font-semibold text-red-600 mb-3">逾期任务</h3>
        <div class="space-y-2">
            {% for t in overdue_tasks %}
            <div class="flex justify-between items-center text-sm">
                <a href="{{ url_for('tasks.detail', id=t.id) }}" class="text-blue-600 hover:underline">{{ t.task_name }}</a>
                <span class="text-red-600 text-xs">目标: {{ t.target_date }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    {% if upcoming_tasks %}
    <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-sm font-semibold text-yellow-600 mb-3">即将到期（7天内）</h3>
        <div class="space-y-2">
            {% for t in upcoming_tasks %}
            <div class="flex justify-between items-center text-sm">
                <a href="{{ url_for('tasks.detail', id=t.id) }}" class="text-blue-600 hover:underline">{{ t.task_name }}</a>
                <span class="text-yellow-600 text-xs">目标: {{ t.target_date }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.2/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script>
// 状态分布饼图
const statusData = {{ status_data | tojson }};
new Chart(document.getElementById('statusChart'), {
    type: 'doughnut',
    data: {
        labels: Object.keys(statusData),
        datasets: [{
            data: Object.values(statusData),
            backgroundColor: ['#e5e7eb', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
        }]
    },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
});

// 优先级柱状图
const priorityData = {{ priority_data | tojson }};
const priorityColors = { Critical: '#ef4444', High: '#f59e0b', Medium: '#3b82f6', Low: '#10b981' };
new Chart(document.getElementById('priorityChart'), {
    type: 'bar',
    data: {
        labels: Object.keys(priorityData),
        datasets: [{
            data: Object.values(priorityData),
            backgroundColor: Object.keys(priorityData).map(k => priorityColors[k] || '#6b7280'),
        }]
    },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
});

// 地点进度堆叠柱状图
const locStats = {{ location_stats | tojson }};
new Chart(document.getElementById('locationChart'), {
    type: 'bar',
    data: {
        labels: locStats.map(s => s[0]),
        datasets: [
            { label: '已完成', data: locStats.map(s => s[2]), backgroundColor: '#10b981' },
            { label: '未完成', data: locStats.map(s => s[1] - s[2]), backgroundColor: '#e5e7eb' },
        ]
    },
    options: { responsive: true, scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1 } } } }
});

function exportPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('l', 'mm', 'a4');
    doc.setFontSize(18);
    doc.text('APAC Infra Task Manager Report', 14, 20);
    doc.setFontSize(10);
    doc.text('Generated: ' + new Date().toLocaleDateString(), 14, 28);

    const charts = document.querySelectorAll('canvas');
    let y = 35;
    charts.forEach((canvas, i) => {
        if (y > 170) { doc.addPage(); y = 20; }
        const img = canvas.toDataURL('image/png');
        doc.addImage(img, 'PNG', 14, y, 120, 70);
        if (i % 2 === 0) y += 75;
        else { doc.addPage(); y = 20; }
    });
    doc.save('task-report-' + new Date().toISOString().slice(0, 10) + '.pdf');
}
</script>
{% endblock %}
```

**Step 3: 更新 base.html 添加 extra_js block**

在 `app/templates/base.html` 的 `</body>` 之前添加：

```html
    {% block extra_js %}{% endblock %}
```

**Step 4: 提交**

```bash
git add app/routes/dashboard.py app/templates/dashboard/ app/static/js/ app/templates/base.html
git commit -m "feat: dashboard with stats cards, charts, alerts, PDF export"
```

---

### Task 8: Excel 导入导出

**Files:**
- Create: `app/services/excel_service.py`
- Create: `app/routes/data_io.py`
- Create: `app/templates/data/index.html`

**Step 1: 创建 excel_service.py**

```python
from datetime import datetime
from openpyxl import Workbook
from openpyxl import load_workbook
from app import db
from app.models import Location, Task, TaskAssignment


LOCATION_HEADERS = [
    "Location ID", "Location Name", "Country", "City", "Location Type",
    "Region", "Is Active", "IT Manager", "Primary IT Contact",
]

TASK_HEADERS = [
    "Task ID", "Task Name", "Task Source", "Stakeholder", "Task Description",
    "Scope Type", "Scope Rule", "Scope Detail", "Task Owner", "Execution Model",
    "Overall Status", "Start Date", "Target Date", "Last Update",
    "Link to File / Collection", "Link to Mail", "Task Priority", "Comments",
]

ASSIGNMENT_HEADERS = [
    "Task ID", "Location ID", "IT Name", "IT Role", "Local Responsibility",
    "Local Status", "Last Update", "Issue / Blocker", "Comments",
]


def export_to_workbook():
    wb = Workbook()

    # Task_Master
    ws_task = wb.active
    ws_task.title = "Task_Master"
    ws_task.append(TASK_HEADERS)
    for t in Task.query.order_by(Task.id):
        ws_task.append([
            t.id, t.task_name, t.task_source, t.stakeholder, t.task_description,
            t.scope_type, t.scope_rule, t.scope_detail, t.task_owner, t.execution_model,
            t.overall_status, str(t.start_date) if t.start_date else "",
            str(t.target_date) if t.target_date else "",
            str(t.last_update) if t.last_update else "",
            t.link_to_file, t.link_to_mail, t.task_priority, t.comments,
        ])

    # Location_Master
    ws_loc = wb.create_sheet("Location_Master")
    ws_loc.append(LOCATION_HEADERS)
    for loc in Location.query.order_by(Location.id):
        ws_loc.append([
            loc.id, loc.location_name, loc.country, loc.city, loc.location_type,
            loc.region, "Yes" if loc.is_active else "No",
            loc.it_manager, loc.primary_it_contact,
        ])

    # Task_Assignment
    ws_assign = wb.create_sheet("Task_Assignment")
    ws_assign.append(ASSIGNMENT_HEADERS)
    for a in TaskAssignment.query.order_by(TaskAssignment.id):
        ws_assign.append([
            a.task_id, a.location_id, a.it_name, a.it_role, a.local_responsibility,
            a.local_status, str(a.last_update) if a.last_update else "",
            a.issue_blocker, a.comments,
        ])

    return wb


def import_from_workbook(wb, sheet_name=None):
    """导入 Excel 数据。返回导入统计 {sheet_name: count}。"""
    stats = {}

    if sheet_name is None or sheet_name == "Location_Master":
        if "Location_Master" in wb.sheetnames:
            ws = wb["Location_Master"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row[1]:
                    continue
                loc = Location(
                    location_name=str(row[1]),
                    country=str(row[2] or ""),
                    city=str(row[3] or ""),
                    location_type=str(row[4] or ""),
                    region=str(row[5] or ""),
                    is_active=str(row[6]).lower() not in ("no", "false", "0"),
                    it_manager=str(row[7] or ""),
                    primary_it_contact=str(row[8] or ""),
                )
                db.session.add(loc)
                count += 1
            stats["Location_Master"] = count

    if sheet_name is None or sheet_name == "Task_Master":
        if "Task_Master" in wb.sheetnames:
            ws = wb["Task_Master"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row[1]:
                    continue
                from datetime import date as date_type
                task = Task(
                    task_name=str(row[1]),
                    task_source=str(row[2] or ""),
                    stakeholder=str(row[3] or ""),
                    task_description=str(row[4] or ""),
                    scope_type=str(row[5] or "Manual"),
                    scope_rule=str(row[6] or ""),
                    scope_detail=str(row[7] or ""),
                    task_owner=str(row[8] or ""),
                    execution_model=str(row[9] or ""),
                    overall_status=str(row[10] or "Not Started"),
                    start_date=_to_date(row[11]),
                    target_date=_to_date(row[12]),
                    last_update=_to_date(row[13]),
                    link_to_file=str(row[14] or ""),
                    link_to_mail=str(row[15] or ""),
                    task_priority=str(row[16] or "Medium"),
                    comments=str(row[17] or ""),
                )
                db.session.add(task)
                count += 1
            stats["Task_Master"] = count

    db.session.commit()
    return stats


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None
```

**Step 2: 创建 data_io.py**

```python
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from openpyxl import load_workbook
from app import db
from app.services.excel_service import export_to_workbook, import_from_workbook

bp = Blueprint("data_io", __name__, url_prefix="/data")


@bp.route("/")
def index():
    return render_template("data/index.html")


@bp.route("/export")
def export_excel():
    wb = export_to_workbook()
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="APAC_Infra_Task_List.xlsx",
    )


@bp.route("/import", methods=["POST"])
def import_excel():
    file = request.files.get("file")
    if not file or not file.filename.endswith((".xlsx", ".xls")):
        flash("请上传 .xlsx 文件", "error")
        return redirect(url_for("data_io.index"))

    sheet = request.form.get("sheet")
    try:
        wb = load_workbook(file)
        stats = import_from_workbook(wb, sheet if sheet else None)
        parts = [f"{k}: {v} 条" for k, v in stats.items()]
        flash(f"导入成功 — {', '.join(parts)}", "success")
    except Exception as e:
        flash(f"导入失败: {e}", "error")

    return redirect(url_for("data_io.index"))
```

**Step 3: 创建 data/index.html**

```html
{% extends "base.html" %}

{% block title %}导入导出 - APAC Task Manager{% endblock %}

{% block content %}
<div class="max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">数据导入导出</h1>

    <div class="grid grid-cols-2 gap-6">
        <!-- 导出 -->
        <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">导出 Excel</h2>
            <p class="text-sm text-gray-600 mb-4">将所有数据导出为 .xlsx 文件，包含 Task_Master、Location_Master、Task_Assignment 三个工作表。</p>
            <a href="{{ url_for('data_io.export_excel') }}" class="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm">导出</a>
        </div>

        <!-- 导入 -->
        <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">导入 Excel</h2>
            <form method="POST" action="{{ url_for('data_io.import_excel') }}" enctype="multipart/form-data" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">选择文件</label>
                    <input type="file" name="file" accept=".xlsx" required class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">导入范围</label>
                    <select name="sheet" class="w-full border rounded-md px-3 py-2 text-sm">
                        <option value="">全部工作表</option>
                        <option value="Location_Master">仅 Location_Master</option>
                        <option value="Task_Master">仅 Task_Master</option>
                    </select>
                </div>
                <button type="submit" class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm">导入</button>
            </form>
            <p class="text-xs text-gray-400 mt-3">注意：导入会新增数据（不会覆盖已有数据）</p>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 4: 提交**

```bash
git add app/services/excel_service.py app/routes/data_io.py app/templates/data/
git commit -m "feat: Excel import/export with sheet selection"
```

---

### Task 9: 集成测试与启动验证

**Files:**
- Modify: `app/__init__.py` — 确保所有 blueprint 注册

**Step 1: 确认 app/__init__.py 完整**

`app/__init__.py` 应包含所有 blueprint 的注册（已在 Task 1 中完成）。确认内容正确。

**Step 2: 初始化数据库并启动**

```bash
rm -f instance/tasks.db
.venv/bin/python -c "from app import create_app; create_app()"
```

**Step 3: 启动应用**

```bash
.venv/bin/python run.py
```

访问 `http://localhost:5000`，验证：
1. 仪表盘页面加载（统计为 0）
2. 点击"地点" → 新建地点 → 保存成功
3. 点击"任务" → 新建任务 → 自动分配
4. 任务详情 → 手动添加/移除分配
5. 导入导出 → 上传原始 xlsx → 导出

**Step 4: 提交**

```bash
git add -A
git commit -m "feat: complete APAC Infra Task Manager v1"
```

---

## 实施顺序总览

| Task | 内容 | 依赖 |
|------|------|------|
| 1 | 项目脚手架 | 无 |
| 2 | 数据模型 | Task 1 |
| 3 | 基础模板 | Task 1 |
| 4 | 范围引擎 | Task 2 |
| 5 | 地点 CRUD | Task 2, 3 |
| 6 | 任务 CRUD | Task 2, 3, 4 |
| 7 | 仪表盘 | Task 2, 3, 6 |
| 8 | Excel 导入导出 | Task 2, 5, 6 |
| 9 | 集成验证 | Task 1-8 |
