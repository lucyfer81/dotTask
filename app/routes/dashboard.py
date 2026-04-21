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

    overdue_tasks = (
        Task.query.filter(
            Task.target_date < today,
            Task.overall_status.notin_(["Completed", "Cancelled"]),
        )
        .order_by(Task.target_date)
        .limit(10)
        .all()
    )

    upcoming_tasks = (
        Task.query.filter(
            Task.target_date.between(today, week_later),
            Task.overall_status.notin_(["Completed", "Cancelled"]),
        )
        .order_by(Task.target_date)
        .all()
    )

    # Chart data
    status_data = (
        db.session.query(Task.overall_status, db.func.count(Task.id))
        .group_by(Task.overall_status)
        .all()
    )
    priority_data = (
        db.session.query(Task.task_priority, db.func.count(Task.id))
        .group_by(Task.task_priority)
        .all()
    )

    # Per-location stats
    location_stats = (
        db.session.query(
            Location.location_name,
            db.func.count(TaskAssignment.id).label("total"),
            db.func.sum(
                db.case((TaskAssignment.local_status == "Completed", 1), else_=0)
            ).label("done"),
        )
        .join(TaskAssignment, TaskAssignment.location_id == Location.id)
        .group_by(Location.id)
        .order_by(db.desc(db.func.count(TaskAssignment.id)))
        .limit(10)
        .all()
    )

    # Convert Row tuples to lists for JSON serialization
    location_stats_json = [[name, total, int(done or 0)] for name, total, done in location_stats]

    return render_template(
        "dashboard/index.html",
        total_tasks=total_tasks,
        in_progress=in_progress,
        completed=completed,
        on_hold=on_hold,
        overdue=overdue,
        blocked=blocked,
        overdue_tasks=overdue_tasks,
        upcoming_tasks=upcoming_tasks,
        status_data=dict(status_data),
        priority_data=dict(priority_data),
        location_stats=location_stats,
        location_stats_json=location_stats_json,
        today=today,
    )
