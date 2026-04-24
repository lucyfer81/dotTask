from flask import Blueprint, render_template
from app.models import Location, Task, TaskAssignment
from app import db

bp = Blueprint("workbench", __name__, url_prefix="/workbench")


@bp.route("/")
def index():
    locations = Location.query.filter_by(is_active=True).order_by(Location.location_name).all()
    tasks = Task.query.order_by(Task.task_name).all()
    return render_template("workbench/index.html", locations=locations, tasks=tasks)
