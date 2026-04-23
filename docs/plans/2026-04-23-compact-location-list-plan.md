# Compact Location List Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the card-based location assignment list with a compact accordion + search/filter UI, making it easy to find specific locations in tasks with many assignments.

**Architecture:** Pure frontend change — client-side JS filtering and accordion expand/collapse. No new backend routes. The existing `detail` and `drawer` routes already provide all data. Each assignment row gets `data-name` and `data-status` attributes for JS filtering.

**Tech Stack:** Jinja2 templates, Tailwind CSS (CDN), vanilla JavaScript, existing HTMX form submission pattern.

---

### Task 1: Add CSS for compact accordion rows

**Files:**
- Modify: `app/static/css/main.css` (append at end)

**Step 1: Add compact row styles**

Append these styles to `app/static/css/main.css`:

```css
/* === 紧凑位置列表 === */
.loc-row {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.75rem;
    cursor: pointer;
    transition: background-color 150ms;
    gap: 0.75rem;
    user-select: none;
}
.loc-row:hover {
    background-color: #f9fafb;
}
.dark .loc-row:hover {
    background-color: #353840;
}
.loc-row.expanded {
    background-color: #f0f7ff;
}
.dark .loc-row.expanded {
    background-color: #1e3a5f;
}
.loc-arrow {
    flex-shrink: 0;
    width: 16px;
    height: 16px;
    color: #9ca3af;
    transition: transform 200ms ease;
}
.loc-row.expanded .loc-arrow {
    transform: rotate(90deg);
}
.loc-name {
    flex: 1;
    min-width: 0;
    font-size: 0.875rem;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.loc-it {
    font-size: 0.75rem;
    color: #6b7280;
    flex-shrink: 0;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.dark .loc-it {
    color: #9ca3af;
}
.loc-remove-btn {
    opacity: 0;
    transition: opacity 150ms;
    flex-shrink: 0;
}
.loc-row:hover .loc-remove-btn {
    opacity: 1;
}
.loc-detail {
    max-height: 0;
    overflow: hidden;
    transition: max-height 300ms ease-out, padding 300ms ease-out;
    background-color: #f9fafb;
    border-top: 0;
}
.dark .loc-detail {
    background-color: #252830;
}
.loc-row-wrapper.expanded .loc-detail {
    max-height: 400px;
    border-top: 1px solid #e5e7eb;
}
.dark .loc-row-wrapper.expanded .loc-detail {
    border-top-color: #373a40;
}
.loc-filter-tab {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 150ms;
    background-color: #f3f4f6;
    color: #4b5563;
}
.dark .loc-filter-tab {
    background-color: #1f2937;
    color: #9ca3af;
}
.loc-filter-tab:hover {
    border-color: #9ca3af;
}
.loc-filter-tab.active {
    background-color: #dbeafe;
    color: #1d4ed8;
    border-color: #93c5fd;
}
.dark .loc-filter-tab.active {
    background-color: #1e3a5f;
    color: #60a5fa;
    border-color: #2563eb;
}
.loc-filter-count {
    font-weight: 600;
}
.progress-clickable {
    cursor: pointer;
    border-radius: 4px;
    padding: 4px 8px;
    margin: -4px -8px;
    transition: background-color 150ms;
}
.progress-clickable:hover {
    background-color: #f3f4f6;
}
.dark .progress-clickable:hover {
    background-color: #353840;
}
.progress-clickable.highlighted {
    background-color: #dbeafe;
}
.dark .progress-clickable.highlighted {
    background-color: #1e3a5f;
}
```

**Step 2: Verify CSS loads**

Run: `bash taskmgr.sh restart` then open browser and confirm no console errors.

**Step 3: Commit**

```bash
git add app/static/css/main.css
git commit -m "style: add compact accordion row CSS for location list"
```

---

### Task 2: Rewrite task detail page location section

**Files:**
- Modify: `app/templates/tasks/detail.html` (lines 141–213, the Location Assignments section)

**Context:** The `detail` route at `app/routes/tasks.py:117-132` already provides `assignments` (list of TaskAssignment), `unassigned_locations`, and `local_status_options`. No route changes needed.

The template currently renders each assignment as a large card (lines 150–185). We replace this entire block.

**Step 1: Replace the Location Assignments section**

In `app/templates/tasks/detail.html`, replace everything from the comment `<!-- Location Assignments -->` (line 142) through the closing `</div>` of the section (line 214) — the entire `<div class="bg-white...">` block that contains "Location Assignments".

Replace with:

```html
            <!-- Location Assignments -->
            <div class="bg-white dark:bg-cc-card shadow-sm rounded-lg border border-gray-200 dark:border-cc-border p-6">
                <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 pb-2 border-b border-gray-200 dark:border-cc-border">
                    Location Assignments
                    <span class="text-sm font-normal text-gray-500 dark:text-gray-400">({{ assignments | length }} locations)</span>
                </h2>

                {% if assignments %}
                <!-- Search & Filter -->
                <div class="mb-4 space-y-3">
                    <input type="text" id="loc-search" placeholder="Search location name..."
                           class="w-full px-3 py-2 border border-gray-300 dark:border-cc-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-cc-bg dark:text-gray-200">
                    <div class="flex flex-wrap gap-2" id="loc-filter-tabs">
                        <button class="loc-filter-tab active" data-filter="">All <span class="loc-filter-count">({{ assignments | length }})</span></button>
                        {% for status_key, status_label, status_count in status_counts %}
                        <button class="loc-filter-tab" data-filter="{{ status_key }}">{{ status_label }} <span class="loc-filter-count">({{ status_count }})</span></button>
                        {% endfor %}
                    </div>
                </div>

                <!-- Compact Location List -->
                <div class="border border-gray-200 dark:border-cc-border rounded-lg divide-y divide-gray-200 dark:divide-cc-border" id="loc-list">
                    {% for assignment in assignments %}
                    <div class="loc-row-wrapper" data-name="{{ assignment.location.location_name }}" data-status="{{ assignment.local_status or 'Pending' }}" data-id="{{ assignment.id }}">
                        <div class="loc-row" onclick="toggleAccordion(this)">
                            <svg class="loc-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                            </svg>
                            <span class="loc-name">{{ assignment.location.location_name }}</span>
                            <span class="badge badge-{{ (assignment.local_status or 'pending') | lower | replace(' ', '-') }}">{{ assignment.local_status or 'Pending' }}</span>
                            <span class="loc-it">{{ assignment.it_name or '' }}</span>
                            <form method="post" action="{{ url_for('tasks.remove_assignment', task_id=task.id, assignment_id=assignment.id) }}" class="loc-remove-btn inline" onclick="event.stopPropagation()" onsubmit="return confirm('Remove this assignment?')">
                                <button type="submit" class="text-xs text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 px-1">Remove</button>
                            </form>
                        </div>
                        <div class="loc-detail">
                            <div class="p-4">
                                <form method="post" action="{{ url_for('tasks.update_assignment', task_id=task.id, assignment_id=assignment.id) }}" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    <div>
                                        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Local Status</label>
                                        <select name="local_status" class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                                            {% for ls in local_status_options %}
                                            <option value="{{ ls }}" {% if (assignment.local_status or 'Pending') == ls %}selected{% endif %}>{{ ls }}</option>
                                            {% endfor %}
                                        </select>
                                    </div>
                                    <div>
                                        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">IT Person</label>
                                        <input type="text" name="it_name" value="{{ assignment.it_name or '' }}"
                                            class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                                    </div>
                                    <div class="sm:col-span-2">
                                        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Task Log</label>
                                        {% if assignment.task_log %}
                                        <div class="mb-2 p-2 bg-gray-50 dark:bg-gray-800 rounded text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-40 overflow-y-auto border border-gray-200 dark:border-cc-border">{{ assignment.task_log }}</div>
                                        {% endif %}
                                        <input type="text" name="task_log_entry" placeholder="Add a log entry..."
                                            class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                                    </div>
                                    <div class="sm:col-span-2 flex justify-end">
                                        <button type="submit" class="px-3 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700">Update</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <p class="mt-3 text-xs text-gray-500 dark:text-gray-400" id="loc-count">Showing {{ assignments | length }} / {{ assignments | length }} locations</p>
                {% else %}
                <p class="text-sm text-gray-500 dark:text-gray-400 py-4">No assignments yet.</p>
                {% endif %}

                <!-- Add Location -->
                {% if unassigned_locations %}
                <div class="mt-4 pt-4 border-t border-gray-200 dark:border-cc-border">
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Add Location</h3>
                    <form method="post" action="{{ url_for('tasks.assign_location', id=task.id) }}" class="flex flex-wrap items-end gap-3">
                        <div class="flex-1 min-w-[200px]">
                            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Select Location</label>
                            <select name="location_id" required class="w-full text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                                <option value="">-- Select Location --</option>
                                {% for loc in unassigned_locations %}
                                <option value="{{ loc.id }}">{{ loc.location_name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">IT Person</label>
                            <input type="text" name="it_name" value="" placeholder="Optional"
                                class="text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                        </div>
                        <button type="submit" class="px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700">Assign</button>
                    </form>
                </div>
                {% endif %}
            </div>
```

**Step 2: Add `status_counts` to the detail route**

In `app/routes/tasks.py`, modify the `detail` function (lines 117–132). We need to compute status counts and pass them to the template. After line 125 (`unassigned_locations = ...`), add the status counting logic and include it in the `render_template` call.

Replace the `detail` function:

```python
@bp.route("/<int:id>")
def detail(id):
    task = Task.query.get_or_404(id)
    assignments = task.assignments.order_by(TaskAssignment.id).all()
    assigned_location_ids = [a.location_id for a in assignments]
    if assigned_location_ids:
        unassigned_locations = Location.query.filter_by(is_active=True).filter(~Location.id.in_(assigned_location_ids)).order_by(Location.location_name).all()
    else:
        unassigned_locations = Location.query.filter_by(is_active=True).order_by(Location.location_name).all()

    local_statuses = get_options("local_statuses")
    status_counts = []
    for s in local_statuses:
        count = sum(1 for a in assignments if (a.local_status or "Pending") == s)
        if count > 0:
            key = s.lower().replace(" ", "-")
            status_counts.append((key, s, count))

    return render_template(
        "tasks/detail.html", task=task, assignments=assignments,
        unassigned_locations=unassigned_locations,
        status_options=get_options("statuses"), priority_options=get_options("priorities"),
        local_status_options=local_statuses, status_counts=status_counts,
    )
```

**Step 3: Add the JavaScript for accordion, search, and filter**

In `app/templates/tasks/detail.html`, add an `{% endblock %}` for content and a new `{% block extra_js %}` section at the end of the file (before the final `{% endblock %}`). The base template has `{% block extra_js %}{% endblock %}` already.

Append after the main content `{% endblock %}` (the one that closes `{% block content %}`):

```html
{% endblock %}

{% block extra_js %}
<script>
(function() {
    var searchInput = document.getElementById('loc-search');
    var filterTabs = document.getElementById('loc-filter-tabs');
    var locList = document.getElementById('loc-list');
    var countDisplay = document.getElementById('loc-count');
    if (!searchInput || !locList) return;

    var rows = locList.querySelectorAll('.loc-row-wrapper');
    var activeFilter = '';
    var total = rows.length;

    function filterLocations() {
        var search = searchInput.value.toLowerCase();
        var visible = 0;
        rows.forEach(function(row) {
            var matchName = row.dataset.name.toLowerCase().indexOf(search) !== -1;
            var matchStatus = !activeFilter || row.dataset.status.toLowerCase().replace(' ', '-') === activeFilter;
            if (matchName && matchStatus) {
                row.style.display = '';
                visible++;
            } else {
                row.style.display = 'none';
                // collapse if expanded and filtered out
                if (row.classList.contains('expanded')) {
                    row.classList.remove('expanded');
                    row.querySelector('.loc-row').classList.remove('expanded');
                }
            }
        });
        if (countDisplay) {
            countDisplay.textContent = 'Showing ' + visible + ' / ' + total + ' locations';
        }
    }

    searchInput.addEventListener('input', filterLocations);

    if (filterTabs) {
        filterTabs.addEventListener('click', function(e) {
            var tab = e.target.closest('.loc-filter-tab');
            if (!tab) return;
            filterTabs.querySelectorAll('.loc-filter-tab').forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            activeFilter = tab.dataset.filter;
            filterLocations();
            // highlight corresponding progress summary row
            document.querySelectorAll('.progress-clickable').forEach(function(el) {
                el.classList.toggle('highlighted', el.dataset.filter === activeFilter && activeFilter !== '');
            });
        });
    }

    // Expose for progress summary clicks and accordion
    window.filterByStatus = function(statusKey) {
        activeFilter = statusKey;
        // update tab UI
        if (filterTabs) {
            filterTabs.querySelectorAll('.loc-filter-tab').forEach(function(t) {
                t.classList.toggle('active', t.dataset.filter === statusKey);
            });
        }
        // clear search
        if (searchInput) searchInput.value = '';
        filterLocations();
        // scroll to list
        locList.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // highlight progress row
        document.querySelectorAll('.progress-clickable').forEach(function(el) {
            el.classList.toggle('highlighted', el.dataset.filter === statusKey);
        });
    };
})();

function toggleAccordion(rowEl) {
    var wrapper = rowEl.closest('.loc-row-wrapper');
    var wasExpanded = wrapper.classList.contains('expanded');
    // collapse all
    document.querySelectorAll('.loc-row-wrapper.expanded').forEach(function(w) {
        w.classList.remove('expanded');
        w.querySelector('.loc-row').classList.remove('expanded');
    });
    // expand clicked (unless it was already open)
    if (!wasExpanded) {
        wrapper.classList.add('expanded');
        rowEl.classList.add('expanded');
    }
}

// Restore expanded state from URL hash
(function() {
    var hash = window.location.hash;
    if (hash && hash.startsWith('#assignment-')) {
        var id = hash.substring('#assignment-'.length);
        var target = document.querySelector('.loc-row-wrapper[data-id="' + id + '"]');
        if (target) {
            target.classList.add('expanded');
            target.querySelector('.loc-row').classList.add('expanded');
            setTimeout(function() {
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        }
    }
})();
</script>
{% endblock %}
```

**Step 4: Make progress summary rows clickable**

In the right panel (Progress Summary section, lines 218–303 of the original `detail.html`), the status count rows need to be wrapped in clickable divs. In the new template, find the lines that look like:

```html
<div class="flex items-center justify-between">
    <span class="text-sm text-gray-600 dark:text-gray-400">
        <span class="badge badge-completed">Completed</span>
    </span>
    <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ ns.completed }}</span>
</div>
```

Replace each of these status rows (Completed, In Progress, Pending, Blocked, N/A) with:

```html
<div class="flex items-center justify-between progress-clickable" data-filter="completed" onclick="filterByStatus('completed')">
    <span class="text-sm text-gray-600 dark:text-gray-400">
        <span class="badge badge-completed">Completed</span>
    </span>
    <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ ns.completed }}</span>
</div>
```

Do the same for each status — use the corresponding filter key (`in-progress`, `pending`, `blocked`, `na`) and badge class.

**Step 5: Restart and visually verify**

Run: `bash taskmgr.sh restart`

Open a task with multiple locations. Verify:
- Each location shows as a single compact line
- Clicking a line expands the edit area below (accordion)
- Search input filters by name
- Status filter tabs work
- Progress summary status rows are clickable and filter the list
- Remove button appears on hover
- URL hash `#assignment-XX` restores expanded state after form submit

**Step 6: Commit**

```bash
git add app/templates/tasks/detail.html app/routes/tasks.py
git commit -m "feat: compact accordion location list with search and filter on task detail page"
```

---

### Task 3: Rewrite drawer location section

**Files:**
- Modify: `app/templates/tasks/partials/drawer.html`

**Context:** The drawer loads via HTMX from route `tasks.drawer` at `app/routes/tasks.py:309-318`. It already provides `assignments`, `local_status_options`. We need to also pass `status_counts` (same as Task 2).

**Step 1: Add `status_counts` to the drawer route**

In `app/routes/tasks.py`, modify the `drawer` function (lines 309–318):

```python
@bp.route("/<int:id>/drawer")
def drawer(id):
    """Return drawer content fragment for HTMX slide-over panel."""
    task = Task.query.get_or_404(id)
    assignments = task.assignments.order_by(TaskAssignment.id).all()
    local_statuses = get_options("local_statuses")
    status_counts = []
    for s in local_statuses:
        count = sum(1 for a in assignments if (a.local_status or "Pending") == s)
        if count > 0:
            key = s.lower().replace(" ", "-")
            status_counts.append((key, s, count))
    return render_template(
        "tasks/partials/drawer.html", task=task, assignments=assignments,
        status_options=get_options("statuses"),
        local_status_options=local_statuses,
        status_counts=status_counts,
    )
```

**Step 2: Replace drawer template**

Replace the entire content of `app/templates/tasks/partials/drawer.html` with:

```html
<div class="p-6 space-y-6">
    <div class="flex items-center justify-between pb-4 border-b border-gray-200 dark:border-cc-border">
        <div>
            <h2 class="text-lg font-bold text-gray-900 dark:text-gray-100">{{ task.task_name }}</h2>
            <div class="flex gap-2 mt-1">
                <span class="badge badge-{{ task.overall_status | lower | replace(' ', '-') }}">{{ task.overall_status }}</span>
                <span class="badge badge-{{ task.task_priority | lower }}">{{ task.task_priority }}</span>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <a href="{{ url_for('tasks.detail', id=task.id) }}" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">Open full page</a>
            <button onclick="closeDrawer()" class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        </div>
    </div>
    <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
            <span class="text-gray-500 dark:text-gray-400">Owner:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-200 font-mono">{{ task.task_owner or '-' }}</span>
        </div>
        <div>
            <span class="text-gray-500 dark:text-gray-400">Target:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-200 font-mono">{{ task.target_date.strftime('%Y-%m-%d') if task.target_date else '-' }}</span>
        </div>
        <div>
            <span class="text-gray-500 dark:text-gray-400">Scope:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-200">{{ task.scope_country or 'All' }} / {{ task.scope_location_type or 'All' }}</span>
        </div>
        <div>
            <span class="text-gray-500 dark:text-gray-400">Execution:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-200">{{ task.execution_model or '-' }}</span>
        </div>
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
    {% if assignments | length > 0 %}
    {% set pct = (ns.completed / (assignments | length) * 100) | int %}
    <div>
        <div class="flex justify-between text-xs mb-1">
            <span class="text-gray-600 dark:text-gray-400">Progress {{ pct }}%</span>
            <span class="text-gray-500 dark:text-gray-500">{{ ns.completed }}/{{ assignments | length }} done</span>
        </div>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div class="bg-green-500 h-2 rounded-full transition-all duration-500" style="width: {{ pct }}%"></div>
        </div>
    </div>
    {% endif %}
    <div>
        <h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3">Locations ({{ assignments | length }})</h3>
        {% if assignments %}
        <!-- Drawer search + status dropdown filter -->
        <div class="mb-3 flex gap-2">
            <input type="text" id="drawer-loc-search" placeholder="Search..."
                   class="flex-1 px-2 py-1 border border-gray-300 dark:border-cc-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
            <select id="drawer-loc-filter" class="text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                <option value="">All ({{ assignments | length }})</option>
                {% for status_key, status_label, status_count in status_counts %}
                <option value="{{ status_key }}">{{ status_label }} ({{ status_count }})</option>
                {% endfor %}
            </select>
        </div>
        <div class="border border-gray-200 dark:border-cc-border rounded-lg divide-y divide-gray-200 dark:divide-cc-border max-h-[50vh] overflow-y-auto" id="drawer-loc-list">
            {% for a in assignments %}
            <div class="drawer-loc-row-wrapper" data-name="{{ a.location.location_name }}" data-status="{{ a.local_status or 'Pending' }}" data-id="{{ a.id }}">
                <div class="loc-row" onclick="toggleDrawerAccordion(this)">
                    <svg class="loc-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                    <span class="loc-name">{{ a.location.location_name }}</span>
                    <span class="badge badge-{{ (a.local_status or 'pending') | lower | replace(' ', '-') }}">{{ a.local_status or 'Pending' }}</span>
                </div>
                <div class="loc-detail">
                    <div class="p-3">
                        <form method="post" action="{{ url_for('tasks.update_assignment', task_id=task.id, assignment_id=a.id) }}" class="space-y-2">
                            <div class="flex gap-2">
                                <select name="local_status" class="flex-1 text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                                    {% for ls in local_status_options %}
                                    <option value="{{ ls }}" {% if (a.local_status or 'Pending') == ls %}selected{% endif %}>{{ ls }}</option>
                                    {% endfor %}
                                </select>
                                <input type="text" name="it_name" value="{{ a.it_name or '' }}" placeholder="IT person"
                                    class="flex-1 text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                            </div>
                            {% if a.task_log %}
                            <div class="p-2 bg-gray-50 dark:bg-gray-800 rounded text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-24 overflow-y-auto border border-gray-200 dark:border-cc-border">{{ a.task_log }}</div>
                            {% endif %}
                            <div class="flex gap-2">
                                <input type="text" name="task_log_entry" placeholder="Add log entry..."
                                    class="flex-1 text-sm border border-gray-300 dark:border-cc-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-cc-bg dark:text-gray-200">
                                <button type="submit" class="px-3 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700">Update</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        <p class="mt-2 text-xs text-gray-500 dark:text-gray-400" id="drawer-loc-count">Showing {{ assignments | length }} / {{ assignments | length }}</p>
        {% else %}
        <p class="text-sm text-gray-500 dark:text-gray-400">No assignments.</p>
        {% endif %}
    </div>
</div>
<script>
// Drawer filtering
(function() {
    var searchInput = document.getElementById('drawer-loc-search');
    var statusFilter = document.getElementById('drawer-loc-filter');
    var locList = document.getElementById('drawer-loc-list');
    var countDisplay = document.getElementById('drawer-loc-count');
    if (!searchInput || !locList) return;

    var rows = locList.querySelectorAll('.drawer-loc-row-wrapper');
    var total = rows.length;

    function filterDrawer() {
        var search = searchInput.value.toLowerCase();
        var status = statusFilter.value;
        var visible = 0;
        rows.forEach(function(row) {
            var matchName = row.dataset.name.toLowerCase().indexOf(search) !== -1;
            var matchStatus = !status || row.dataset.status.toLowerCase().replace(' ', '-') === status;
            if (matchName && matchStatus) {
                row.style.display = '';
                visible++;
            } else {
                row.style.display = 'none';
                if (row.classList.contains('expanded')) {
                    row.classList.remove('expanded');
                    row.querySelector('.loc-row').classList.remove('expanded');
                }
            }
        });
        if (countDisplay) {
            countDisplay.textContent = 'Showing ' + visible + ' / ' + total;
        }
    }

    searchInput.addEventListener('input', filterDrawer);
    statusFilter.addEventListener('change', filterDrawer);
})();

function toggleDrawerAccordion(rowEl) {
    var wrapper = rowEl.closest('.drawer-loc-row-wrapper');
    var wasExpanded = wrapper.classList.contains('expanded');
    document.querySelectorAll('.drawer-loc-row-wrapper.expanded').forEach(function(w) {
        w.classList.remove('expanded');
        w.querySelector('.loc-row').classList.remove('expanded');
    });
    if (!wasExpanded) {
        wrapper.classList.add('expanded');
        rowEl.classList.add('expanded');
    }
}
</script>
```

**Step 3: Restart and test the drawer**

Run: `bash taskmgr.sh restart`

Open task list, click a task name to open the drawer. Verify:
- Compact location rows display correctly
- Search input filters locations
- Status dropdown filters locations
- Clicking a row expands inline edit form (accordion)
- Form submission works (Update button)
- Drawer scrolls properly for many locations

**Step 4: Commit**

```bash
git add app/templates/tasks/partials/drawer.html app/routes/tasks.py
git commit -m "feat: compact accordion location list in task drawer with search and filter"
```

---

### Task 4: Form POST redirect preserves expanded row

**Files:**
- Modify: `app/routes/tasks.py` — `update_assignment` function (lines 220–236)
- Modify: `app/routes/tasks.py` — `remove_assignment` function (lines 239–245)

**Context:** When a user edits an assignment and clicks Update, the page reloads and scrolls to the top. We want it to scroll back to the edited assignment row, expanded.

**Step 1: Update `update_assignment` redirect to include hash**

In `app/routes/tasks.py`, find the `update_assignment` function and change its redirect:

```python
return redirect(url_for('tasks.detail', id=task_id) + f'#assignment-{assignment_id}')
```

**Step 2: Update `remove_assignment` to not need hash (it removes the row, so no need)**

No change needed for `remove_assignment`.

**Step 3: Restart and test**

Run: `bash taskmgr.sh restart`

1. Open a task detail page
2. Expand a location row
3. Change status and click Update
4. Page reloads → the edited row should auto-expand and scroll into view

**Step 4: Commit**

```bash
git add app/routes/tasks.py
git commit -m "fix: preserve expanded location row after form submission via URL hash"
```

---

### Task 5: Visual QA and cleanup

**Step 1: Manual QA on both screen sizes**

Test on 14-inch laptop (viewport ~1366x768) and 24-inch monitor (viewport ~1920x1080):

On the task detail page:
- [ ] Compact rows render correctly (single line, no wrapping)
- [ ] Search filters immediately as you type
- [ ] Status filter tabs work individually
- [ ] Search + status filter combine correctly
- [ ] Accordion expand/collapse works (only one at a time)
- [ ] Expanded edit area shows correctly (status dropdown, IT input, log, Update button)
- [ ] Remove button only shows on row hover
- [ ] Progress summary rows are clickable and filter the list
- [ ] "Showing X / Y" count updates correctly
- [ ] After form submit, the edited row is re-expanded
- [ ] "Add Location" section still works

In the drawer:
- [ ] Compact rows render in the 600px wide drawer
- [ ] Search and status dropdown filter work
- [ ] Accordion works inside the drawer
- [ ] Scrolling works within `max-h-[50vh]`
- [ ] Form submission redirects to full detail page with hash

Light mode and dark mode:
- [ ] All styles render correctly in both themes
- [ ] No contrast issues

**Step 2: Fix any visual issues found**

Adjust CSS or template as needed.

**Step 3: Final commit**

```bash
git add -A
git commit -m "style: polish compact location list UI"
```
