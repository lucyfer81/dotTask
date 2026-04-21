from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Location, TaskAssignment, Task
from app.dropdowns import get_options

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
            comments=request.form.get("comments", ""),
        )
        db.session.add(loc)
        db.session.commit()
        flash("Location created", "success")
        return redirect(url_for("locations.list"))

    return render_template("locations/form.html", location=None, countries=get_options("countries"), location_types=get_options("location_types"))


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
        loc.comments = request.form.get("comments", "")
        db.session.commit()
        flash("Location updated", "success")
        return redirect(url_for("locations.list"))

    return render_template("locations/form.html", location=loc, countries=get_options("countries"), location_types=get_options("location_types"))


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    loc = Location.query.get_or_404(id)
    TaskAssignment.query.filter_by(location_id=id).delete()
    db.session.delete(loc)
    db.session.commit()
    flash("Location deleted", "success")
    return redirect(url_for("locations.list"))


@bp.route("/<int:id>/toggle-active", methods=["POST"])
def toggle_active(id):
    loc = Location.query.get_or_404(id)
    loc.is_active = not loc.is_active
    db.session.commit()
    status = "activated" if loc.is_active else "deactivated"
    flash(f"Location {loc.location_name} {status}", "success")
    return redirect(url_for("locations.list"))
