from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Location, TaskAssignment
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
