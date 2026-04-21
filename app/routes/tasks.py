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
        today=date.today(),
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

        # Auto-assign based on scope
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
    if assigned_location_ids:
        unassigned_locations = Location.query.filter_by(is_active=True).filter(~Location.id.in_(assigned_location_ids)).order_by(Location.location_name).all()
    else:
        unassigned_locations = Location.query.filter_by(is_active=True).order_by(Location.location_name).all()

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
    task = Task.query.get_or_404(id)
    new_status = request.form.get("overall_status")
    if new_status in STATUS_OPTIONS:
        task.overall_status = new_status
        task.last_update = date.today()
        db.session.commit()
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
            flash("已分配地点", "success")
    return redirect(url_for("tasks.detail", id=id))


@bp.route("/<int:task_id>/assignment/<int:assignment_id>", methods=["POST"])
def update_assignment(task_id, assignment_id):
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
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash("已移除分配", "success")
    return redirect(url_for("tasks.detail", id=task_id))


@bp.route("/scope-preview", methods=["POST"])
def scope_preview():
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
