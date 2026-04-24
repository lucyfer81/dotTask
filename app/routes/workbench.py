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
    opt_type = request.args.get("type", "")
    filter_id = request.args.get("filter_id", type=int)
    current_id = request.args.get("current_id", type=int)

    if opt_type == "task" and filter_id:
        assignments = TaskAssignment.query.filter_by(location_id=filter_id).all()
        task_ids = [a.task_id for a in assignments]
        tasks = Task.query.filter(Task.id.in_(task_ids)).order_by(Task.task_name).all() if task_ids else []
        return render_template("workbench/partials/_options.html", items=tasks, value_attr="id", label_attr="task_name", current_id=current_id)

    if opt_type == "location" and filter_id:
        assignments = TaskAssignment.query.filter_by(task_id=filter_id).all()
        loc_ids = [a.location_id for a in assignments]
        locations = Location.query.filter(Location.id.in_(loc_ids)).order_by(Location.location_name).all() if loc_ids else []
        return render_template("workbench/partials/_options.html", items=locations, value_attr="id", label_attr="location_name", current_id=current_id)

    return ""


@bp.route("/content")
def content():
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
