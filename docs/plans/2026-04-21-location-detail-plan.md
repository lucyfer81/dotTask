# Location Detail Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Location detail page that shows all Tasks assigned to a Location, with full edit capability and the ability to add new Task assignments.

**Architecture:** New routes in `locations.py` mirror the assignment CRUD pattern from `tasks.py`. New template `detail.html` mirrors the layout of `tasks/detail.html` but reversed. Location list page links names to the new detail page.

**Tech Stack:** Flask, SQLAlchemy, Jinja2, Tailwind CSS

---

### Task 1: Add detail route to locations.py

**Files:**
- Modify: `app/routes/locations.py`

**Step 1: Add the detail view route**

Add this route after the `list` route (after line 33):

```python
@bp.route("/<int:id>")
def detail(id):
    loc = Location.query.get_or_404(id)
    assignments = (
        TaskAssignment.query
        .filter_by(location_id=id)
        .order_by(TaskAssignment.id)
        .all()
    )
    assigned_task_ids = [a.task_id for a in assignments]
    if assigned_task_ids:
        unassigned_tasks = Task.query.filter(~Task.id.in_(assigned_task_ids)).order_by(Task.task_name).all()
    else:
        unassigned_tasks = Task.query.order_by(Task.task_name).all()

    return render_template(
        "locations/detail.html", location=loc, assignments=assignments,
        unassigned_tasks=unassigned_tasks,
        local_status_options=get_options("local_statuses"),
    )
```

Also add `Task` to the imports at line 3:
```python
from app.models import Location, TaskAssignment, Task
```

**Step 2: Verify the app starts**

Run: `cd /home/ubuntu/my-repos/dotTask && python -c "from app import create_app; app = create_app(); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add app/routes/locations.py
git commit -m "feat: add location detail route"
```

---

### Task 2: Add assignment CRUD routes to locations.py

**Files:**
- Modify: `app/routes/locations.py`

**Step 1: Add three assignment routes**

Add these after the `detail` route. They mirror the logic in `tasks.py` lines 153-198 but redirect back to `locations.detail`:

```python
@bp.route("/<int:id>/assign", methods=["POST"])
def assign_task(id):
    loc = Location.query.get_or_404(id)
    task_id = request.form.get("task_id", type=int)
    if task_id:
        existing = TaskAssignment.query.filter_by(task_id=task_id, location_id=id).first()
        if not existing:
            assignment = TaskAssignment(
                task_id=task_id,
                location_id=id,
                it_name=request.form.get("it_name", ""),
                it_role=request.form.get("it_role", ""),
                local_responsibility=request.form.get("local_responsibility", ""),
            )
            db.session.add(assignment)
            db.session.commit()
            flash("Task assigned", "success")
    return redirect(url_for("locations.detail", id=id))


@bp.route("/<int:loc_id>/assignment/<int:assignment_id>", methods=["POST"])
def update_assignment(loc_id, assignment_id):
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    assignment.local_status = request.form.get("local_status", assignment.local_status)
    new_log = request.form.get("task_log_entry", "").strip()
    if new_log:
        from datetime import datetime as dt
        timestamp = dt.now().strftime("[%Y-%m-%d %H:%M]")
        entry = f"{timestamp} {new_log}"
        if assignment.task_log:
            assignment.task_log += f"\n{entry}"
        else:
            assignment.task_log = entry
    assignment.it_name = request.form.get("it_name", assignment.it_name or "")
    assignment.last_update = date.today()
    db.session.commit()
    flash("Assignment updated", "success")
    return redirect(url_for("locations.detail", id=loc_id))


@bp.route("/<int:loc_id>/assignment/<int:assignment_id>/delete", methods=["POST"])
def remove_assignment(loc_id, assignment_id):
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash("Assignment removed", "success")
    return redirect(url_for("locations.detail", id=loc_id))
```

Add `date` import — update the existing flask import line or add:
```python
from datetime import date
```

**Step 2: Verify app starts**

Run: `python -c "from app import create_app; app = create_app(); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add app/routes/locations.py
git commit -m "feat: add location assignment CRUD routes"
```

---

### Task 3: Create location detail template

**Files:**
- Create: `app/templates/locations/detail.html`

**Step 1: Create the template**

This mirrors `app/templates/tasks/detail.html` but reversed — Location info on the left with Task assignments, progress summary on the right.

```html
{% extends "base.html" %}

{% block title %}{{ location.location_name }} - APAC Task Manager{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <h1 class="text-2xl font-bold text-gray-900">{{ location.location_name }}</h1>
            {% if location.is_active %}
            <span class="badge badge-completed">Active</span>
            {% else %}
            <span class="badge badge-cancelled">Inactive</span>
            {% endif %}
        </div>
        <div class="flex items-center space-x-2">
            <a href="{{ url_for('locations.edit', id=location.id) }}" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
                Edit
            </a>
            <form method="post" action="{{ url_for('locations.delete', id=location.id) }}" class="inline" onsubmit="return confirm('Are you sure you want to delete location &quot;{{ location.location_name }}&quot;?')">
                <button type="submit" class="inline-flex items-center px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                    Delete
                </button>
            </form>
            <a href="{{ url_for('locations.list') }}" class="inline-flex items-center px-4 py-2 bg-white text-gray-700 text-sm font-medium rounded-md border border-gray-300 hover:bg-gray-50">Back to List</a>
        </div>
    </div>

    <!-- Main Content: Two-column Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left: Basic Info + Task Assignment List -->
        <div class="lg:col-span-2 space-y-6">
            <!-- Basic Info -->
            <div class="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
                <h2 class="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">Basic Info</h2>
                <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
                    <div>
                        <dt class="text-sm font-medium text-gray-500">Country</dt>
                        <dd class="text-sm text-gray-900 mt-1">{{ location.country or '-' }}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-500">City</dt>
                        <dd class="text-sm text-gray-900 mt-1">{{ location.city or '-' }}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-500">Location Type</dt>
                        <dd class="text-sm text-gray-900 mt-1">{{ location.location_type or '-' }}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-500">Region</dt>
                        <dd class="text-sm text-gray-900 mt-1">{{ location.region or '-' }}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-500">IT Manager</dt>
                        <dd class="text-sm text-gray-900 mt-1">{{ location.it_manager or '-' }}</dd>
                    </div>
                    <div>
                        <dt class="text-sm font-medium text-gray-500">Primary IT Contact</dt>
                        <dd class="text-sm text-gray-900 mt-1">{{ location.primary_it_contact or '-' }}</dd>
                    </div>
                    {% if location.comments %}
                    <div class="sm:col-span-2">
                        <dt class="text-sm font-medium text-gray-500">Comments</dt>
                        <dd class="text-sm text-gray-900 mt-1 whitespace-pre-wrap">{{ location.comments }}</dd>
                    </div>
                    {% endif %}
                </dl>
            </div>

            <!-- Task Assignments -->
            <div class="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
                <h2 class="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">
                    Task Assignments
                    <span class="text-sm font-normal text-gray-500">({{ assignments | length }} tasks)</span>
                </h2>

                {% if assignments %}
                <div class="space-y-4">
                    {% for assignment in assignments %}
                    <div class="border border-gray-200 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-3">
                            <a href="{{ url_for('tasks.detail', id=assignment.task.id) }}" class="text-sm font-semibold text-blue-700 hover:text-blue-900">{{ assignment.task.task_name }}</a>
                            <form method="post" action="{{ url_for('locations.remove_assignment', loc_id=location.id, assignment_id=assignment.id) }}" class="inline" onsubmit="return confirm('Are you sure you want to remove this assignment?')">
                                <button type="submit" class="text-xs text-red-600 hover:text-red-800">Remove</button>
                            </form>
                        </div>
                        <div class="flex items-center gap-2 mb-3">
                            <span class="badge badge-{{ assignment.task.overall_status | lower | replace(' ', '-') }}">{{ assignment.task.overall_status }}</span>
                            <span class="badge badge-{{ assignment.task.task_priority | lower }}">{{ assignment.task.task_priority }}</span>
                        </div>
                        <form method="post" action="{{ url_for('locations.update_assignment', loc_id=location.id, assignment_id=assignment.id) }}" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                                <label class="block text-xs font-medium text-gray-500 mb-1">Local Status</label>
                                <select name="local_status" class="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500">
                                    {% for ls in local_status_options %}
                                    <option value="{{ ls }}" {% if assignment.local_status == ls %}selected{% endif %}>{{ ls }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-500 mb-1">IT Person</label>
                                <input type="text" name="it_name" value="{{ assignment.it_name or '' }}"
                                    class="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500">
                            </div>
                            <div class="sm:col-span-2">
                                <label class="block text-xs font-medium text-gray-500 mb-1">Task Log</label>
                                {% if assignment.task_log %}
                                <div class="mb-2 p-2 bg-gray-50 rounded text-xs text-gray-700 whitespace-pre-wrap max-h-40 overflow-y-auto border border-gray-200">{{ assignment.task_log }}</div>
                                {% endif %}
                                <input type="text" name="task_log_entry" placeholder="Add a log entry..."
                                    class="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500">
                            </div>
                            <div class="sm:col-span-2 flex justify-end">
                                <button type="submit" class="px-3 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700">Update</button>
                            </div>
                        </form>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <p class="text-sm text-gray-500 py-4">No task assignments yet.</p>
                {% endif %}

                <!-- Add Task -->
                {% if unassigned_tasks %}
                <div class="mt-4 pt-4 border-t border-gray-200">
                    <h3 class="text-sm font-semibold text-gray-700 mb-3">Add Task</h3>
                    <form method="post" action="{{ url_for('locations.assign_task', id=location.id) }}" class="flex flex-wrap items-end gap-3">
                        <div class="flex-1 min-w-[200px]">
                            <label class="block text-xs font-medium text-gray-500 mb-1">Select Task</label>
                            <select name="task_id" required class="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500">
                                <option value="">-- Select Task --</option>
                                {% for t in unassigned_tasks %}
                                <option value="{{ t.id }}">{{ t.task_name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-gray-500 mb-1">IT Person</label>
                            <input type="text" name="it_name" value="" placeholder="Optional"
                                class="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500">
                        </div>
                        <button type="submit" class="px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700">Assign</button>
                    </form>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- Right: Progress Summary -->
        <div class="space-y-6">
            <div class="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
                <h2 class="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-200">Progress Summary</h2>

                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600">Total Assignments</span>
                        <span class="text-sm font-semibold text-gray-900">{{ assignments | length }}</span>
                    </div>

                    {% set ns = namespace(completed=0, in_progress=0, pending=0, blocked=0, na=0) %}
                    {% for a in assignments %}
                        {% if a.local_status == 'Completed' %}{% set ns.completed = ns.completed + 1 %}
                        {% elif a.local_status == 'In Progress' %}{% set ns.in_progress = ns.in_progress + 1 %}
                        {% elif a.local_status == 'Pending' %}{% set ns.pending = ns.pending + 1 %}
                        {% elif a.local_status == 'Blocked' %}{% set ns.blocked = ns.blocked + 1 %}
                        {% elif a.local_status == 'N/A' %}{% set ns.na = ns.na + 1 %}
                        {% endif %}
                    {% endfor %}

                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600"><span class="badge badge-completed">Completed</span></span>
                        <span class="text-sm font-semibold text-gray-900">{{ ns.completed }}</span>
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600"><span class="badge badge-in-progress">In Progress</span></span>
                        <span class="text-sm font-semibold text-gray-900">{{ ns.in_progress }}</span>
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600"><span class="badge badge-pending">Pending</span></span>
                        <span class="text-sm font-semibold text-gray-900">{{ ns.pending }}</span>
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600"><span class="badge badge-blocked">Blocked</span></span>
                        <span class="text-sm font-semibold text-gray-900">{{ ns.blocked }}</span>
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600"><span class="badge badge-na">N/A</span></span>
                        <span class="text-sm font-semibold text-gray-900">{{ ns.na }}</span>
                    </div>

                    <!-- Progress Bar -->
                    {% if assignments | length > 0 %}
                    {% set pct = (ns.completed / (assignments | length) * 100) | int %}
                    <div class="mt-4">
                        <div class="flex items-center justify-between mb-1">
                            <span class="text-xs font-medium text-gray-600">Progress</span>
                            <span class="text-xs font-medium text-gray-600">{{ pct }}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div class="bg-green-500 h-2 rounded-full" style="width: {{ pct }}%"></div>
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Blocker Alert -->
            {% if ns.blocked > 0 %}
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-red-800 mb-2">
                    <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                    </svg>
                    {{ ns.blocked }} task(s) blocked
                </h3>
                <ul class="text-sm text-red-700 space-y-1">
                    {% for a in assignments %}
                    {% if a.local_status == 'Blocked' %}
                    <li>{{ a.task.task_name }}</li>
                    {% endif %}
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

**Step 2: Commit**

```bash
git add app/templates/locations/detail.html
git commit -m "feat: add location detail template with task assignments"
```

---

### Task 4: Update location list page to link to detail

**Files:**
- Modify: `app/templates/locations/list.html:55`

**Step 1: Make location name a link**

Change line 55 from:
```html
<td class="px-4 py-3 text-sm font-medium text-gray-900">{{ loc.location_name }}</td>
```
To:
```html
<td class="px-4 py-3 text-sm font-medium text-blue-700 hover:text-blue-900"><a href="{{ url_for('locations.detail', id=loc.id) }}">{{ loc.location_name }}</a></td>
```

**Step 2: Commit**

```bash
git add app/templates/locations/list.html
git commit -m "feat: link location names to detail page"
```

---

### Task 5: Manual verification

**Step 1: Start the dev server**

Run: `cd /home/ubuntu/my-repos/dotTask && python run.py`

**Step 2: Verify in browser**

1. Open `/locations/` — location names should be clickable links
2. Click a location name — should open detail page at `/locations/<id>`
3. Detail page shows Location info + Task assignments list
4. Can edit local status, IT person, add log entries
5. Can remove an assignment
6. Can add a new Task assignment
7. Progress summary and blocker alert display correctly
8. Task name links navigate to `/tasks/<id>` — the reverse view still works

**Step 3: Final commit if any fixes needed**
