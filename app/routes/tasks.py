import json
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Task, TaskAssignment, Location
from app.services.scope_engine import get_scope_preview, get_distinct_countries
from app.dropdowns import get_options

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


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
    if request.headers.get("HX-Request"):
        return render_template(
            "tasks/partials/task_rows.html", tasks=tasks, today=date.today(),
            status_options=get_options("statuses"),
        )

    return render_template(
        "tasks/list.html",
        tasks=tasks, search=search, status=status, priority=priority,
        status_options=get_options("statuses"), priority_options=get_options("priorities"),
        today=date.today(),
    )


@bp.route("/kanban")
def kanban():
    location_id = request.args.get("location_id", type=int)
    locations = Location.query.filter_by(is_active=True).order_by(Location.location_name).all()

    if location_id:
        location = Location.query.get_or_404(location_id)
        assignments = TaskAssignment.query.filter_by(location_id=location_id).all()
        columns = {}
        local_statuses = get_options("local_statuses")
        for s in local_statuses:
            columns[s] = [a for a in assignments if a.local_status == s]
        default_status = "Pending"
        unmatched = [a for a in assignments if not a.local_status or a.local_status not in columns]
        if unmatched:
            columns.setdefault(default_status, []).extend(unmatched)
        return render_template("tasks/kanban.html", columns=columns, locations=locations,
                             location=location, filtered=True)

    tasks = Task.query.order_by(Task.created_at.desc()).all()
    columns = {}
    for s in get_options("statuses"):
        columns[s] = [t for t in tasks if t.overall_status == s]
    return render_template("tasks/kanban.html", columns=columns, locations=locations,
                         location=None, filtered=False)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        task = Task(
            task_name=request.form["task_name"],
            task_source=request.form.get("task_source", ""),
            stakeholder=request.form.get("stakeholder", ""),
            task_description=request.form.get("task_description", ""),
            scope_country=request.form.get("scope_country", "") or None,
            scope_location_type=request.form.get("scope_location_type", "") or None,
            task_owner=request.form.get("task_owner", ""),
            execution_model=request.form.get("execution_model", ""),
            overall_status=request.form.get("overall_status", "Not Started"),
            start_date=_parse_date(request.form.get("start_date")),
            target_date=_parse_date(request.form.get("target_date")),
            last_update=date.today(),
            link_to_file=json.dumps(_parse_links(request.form.get("file_links_json", "")), ensure_ascii=False) or None,
            link_to_mail=json.dumps(_parse_links(request.form.get("mail_links_json", "")), ensure_ascii=False) or None,
            task_priority=request.form.get("task_priority", "Medium"),
            comments=request.form.get("comments", ""),
        )
        db.session.add(task)
        db.session.flush()

        selected_ids = request.form.getlist("selected_locations", type=int)
        for loc_id in selected_ids:
            assignment = TaskAssignment(task_id=task.id, location_id=loc_id)
            db.session.add(assignment)

        db.session.commit()
        flash("Task created", "success")
        return redirect(url_for("tasks.detail", id=task.id))

    return render_template(
        "tasks/form.html", task=None,
        status_options=get_options("statuses"), priority_options=get_options("priorities"),
        countries=get_distinct_countries(), location_types=get_options("location_types"),
    )


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


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    task = Task.query.get_or_404(id)
    if request.method == "POST":
        task.task_name = request.form["task_name"]
        task.task_source = request.form.get("task_source", "")
        task.stakeholder = request.form.get("stakeholder", "")
        task.task_description = request.form.get("task_description", "")
        task.scope_country = request.form.get("scope_country", "") or None
        task.scope_location_type = request.form.get("scope_location_type", "") or None
        task.task_owner = request.form.get("task_owner", "")
        task.execution_model = request.form.get("execution_model", "")
        task.overall_status = request.form.get("overall_status", "Not Started")
        task.start_date = _parse_date(request.form.get("start_date"))
        task.target_date = _parse_date(request.form.get("target_date"))
        task.last_update = date.today()
        task.link_to_file = json.dumps(_parse_links(request.form.get("file_links_json", "")), ensure_ascii=False) or None
        task.link_to_mail = json.dumps(_parse_links(request.form.get("mail_links_json", "")), ensure_ascii=False) or None
        task.task_priority = request.form.get("task_priority", "Medium")
        task.comments = request.form.get("comments", "")
        db.session.commit()
        flash("Task updated", "success")
        return redirect(url_for("tasks.detail", id=task.id))

    return render_template(
        "tasks/form.html", task=task,
        status_options=get_options("statuses"), priority_options=get_options("priorities"),
        countries=get_distinct_countries(), location_types=get_options("location_types"),
    )


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted", "success")
    return redirect(url_for("tasks.list"))


@bp.route("/<int:id>/status", methods=["POST"])
def update_status(id):
    loc_id = request.form.get("location_id", type=int)
    if loc_id:
        assignment = TaskAssignment.query.filter_by(task_id=id, location_id=loc_id).first_or_404()
        new_status = request.form.get("local_status")
        if new_status in get_options("local_statuses"):
            assignment.local_status = new_status
            assignment.last_update = date.today()
            db.session.commit()
        return redirect(request.headers.get("Referer", url_for("tasks.kanban", location_id=loc_id)))

    task = Task.query.get_or_404(id)
    new_status = request.form.get("overall_status")
    if new_status in get_options("statuses"):
        task.overall_status = new_status
        task.last_update = date.today()
        db.session.commit()

    if request.headers.get("HX-Request"):
        return render_template("tasks/partials/status_menu.html", task=task, status_options=get_options("statuses"))

    return redirect(request.headers.get("Referer", url_for("tasks.list")))


@bp.route("/<int:id>/assign", methods=["POST"])
def assign_location(id):
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
            flash("Location assigned", "success")
    return redirect(url_for("tasks.detail", id=id))


@bp.route("/<int:task_id>/assignment/<int:assignment_id>", methods=["POST"])
def update_assignment(task_id, assignment_id):
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    assignment.local_status = request.form.get("local_status", assignment.local_status)
    new_log = request.form.get("task_log_entry", "").strip()
    if new_log:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M]")
        entry = f"{timestamp} {new_log}"
        if assignment.task_log:
            assignment.task_log += f"\n{entry}"
        else:
            assignment.task_log = entry
    assignment.it_name = request.form.get("it_name", assignment.it_name or "")
    assignment.last_update = date.today()
    db.session.commit()
    flash("Assignment updated", "success")
    return redirect(url_for("tasks.detail", id=task_id) + f"#assignment-{assignment_id}")


@bp.route("/<int:task_id>/assignment/<int:assignment_id>/delete", methods=["POST"])
def remove_assignment(task_id, assignment_id):
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash("Assignment removed", "success")
    return redirect(url_for("tasks.detail", id=task_id))


@bp.route("/scope-preview", methods=["POST"])
def scope_preview():
    country = request.form.get("scope_country", "")
    location_type = request.form.get("scope_location_type", "")
    preview = get_scope_preview(country or None, location_type or None)
    return jsonify(preview)


def _parse_date(value):
    if value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


@bp.route("/<int:id>/status-menu")
def status_menu(id):
    """Return status popup menu fragment for HTMX."""
    task = Task.query.get_or_404(id)
    return render_template("tasks/partials/status_menu.html", task=task, status_options=get_options("statuses"))


@bp.route("/<int:id>/edit-field")
def edit_field(id):
    """Return inline edit form fragment for HTMX."""
    task = Task.query.get_or_404(id)
    field = request.args.get("field")
    allowed = {"task_description", "comments"}
    if field not in allowed:
        return "", 400
    value = getattr(task, field) or ""
    return render_template("tasks/partials/edit_field.html", task=task, field=field, value=value)


@bp.route("/<int:id>/display-field")
def display_field(id):
    """Return display fragment for HTMX (cancel edit)."""
    task = Task.query.get_or_404(id)
    field = request.args.get("field")
    allowed = {"task_description", "comments"}
    if field not in allowed:
        return "", 400
    return render_template("tasks/partials/display_field.html", task=task, field=field)


@bp.route("/<int:id>/save-field", methods=["POST"])
def save_field(id):
    """Save inline edit and return display fragment for HTMX."""
    task = Task.query.get_or_404(id)
    field = request.form.get("field")
    allowed = {"task_description", "comments"}
    if field not in allowed:
        return "", 400
    setattr(task, field, request.form.get("value", ""))
    task.last_update = date.today()
    db.session.commit()
    return render_template("tasks/partials/display_field.html", task=task, field=field)


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


def _parse_links(json_str):
    """Parse JSON links string into list of {"name": ..., "url": ...} dicts.
    Filter out entries with empty url."""
    if not json_str:
        return []
    try:
        links = json.loads(json_str)
        return [l for l in links if l.get("url", "").strip()]
    except (json.JSONDecodeError, TypeError):
        return []
