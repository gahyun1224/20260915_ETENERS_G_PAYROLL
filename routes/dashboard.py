from flask import Blueprint, render_template, request
from flask_login import login_required

from models.batch import Batch
from models.validation import ValidationResult

bp = Blueprint("dashboard", __name__)

STATUS_PRIORITY = {"ERROR": 0, "REVIEW": 1, "NORMAL": 2}


@bp.route("/dashboard")
@bp.route("/")
@login_required
def index():
    latest = Batch.query.order_by(Batch.created_at.desc()).first()
    if latest is None:
        return render_template("dashboard.html", batch=None, results=[], status_filter="ALL", q="")
    return view_batch(latest.id)


@bp.route("/dashboard/<int:batch_id>")
@login_required
def view_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)

    status_filter = request.args.get("status", "ALL")
    q = request.args.get("q", "").strip()

    query = ValidationResult.query.filter_by(batch_id=batch_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (ValidationResult.employee_id.ilike(like)) | (ValidationResult.employee_name.ilike(like))
        )
    results = query.all()
    results.sort(key=lambda r: (STATUS_PRIORITY.get(r.status, 9), r.employee_id))

    if status_filter != "ALL":
        results = [r for r in results if r.status == status_filter]

    return render_template(
        "dashboard.html", batch=batch, results=results, status_filter=status_filter, q=q
    )


@bp.route("/employee/<int:result_id>")
@login_required
def employee_detail(result_id):
    result = ValidationResult.query.get_or_404(result_id)
    return render_template("employee_detail.html", result=result)
