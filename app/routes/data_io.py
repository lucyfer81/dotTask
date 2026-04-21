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
        flash("Please upload a .xlsx file", "error")
        return redirect(url_for("data_io.index"))

    sheet = request.form.get("sheet")
    try:
        wb = load_workbook(file)
        stats = import_from_workbook(wb, sheet if sheet else None)
        parts = [f"{k}: {v} records" for k, v in stats.items()]
        flash(f"Import successful — {', '.join(parts)}", "success")
    except Exception as e:
        flash(f"Import failed: {e}", "error")

    return redirect(url_for("data_io.index"))
