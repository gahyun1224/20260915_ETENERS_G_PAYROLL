from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from decorators import admin_required
from extensions import db
from models.rule import RuleTable
from services.pension_validator import INSURANCE_TYPE

bp = Blueprint("rules", __name__)


@bp.route("/rules", methods=["GET", "POST"])
@login_required
@admin_required
def index():
    if request.method == "POST":
        try:
            effective_start = datetime.strptime(request.form["effective_start"], "%Y-%m-%d").date()
            employee_rate = float(request.form["employee_rate"]) / 100
            lower_limit = float(request.form["lower_limit"])
            upper_limit = float(request.form["upper_limit"])
        except (KeyError, ValueError):
            flash("입력값을 확인해주세요.", "danger")
            return redirect(url_for("rules.index"))

        current = (
            RuleTable.query.filter_by(insurance_type=INSURANCE_TYPE, effective_end=None)
            .order_by(RuleTable.effective_start.desc())
            .first()
        )
        if current:
            current.effective_end = effective_start - timedelta(days=1)

        new_rule = RuleTable(
            insurance_type=INSURANCE_TYPE,
            rule_type="STANDARD",
            effective_start=effective_start,
            effective_end=None,
            employee_rate=employee_rate,
            employer_rate=employee_rate,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            description=request.form.get("description", ""),
            legal_basis=request.form.get("legal_basis", ""),
            source_name=request.form.get("source_name", ""),
            source_url=request.form.get("source_url", ""),
        )
        db.session.add(new_rule)
        db.session.commit()
        flash("새 기준이 등록되었습니다.", "success")
        return redirect(url_for("rules.index"))

    rules = RuleTable.query.order_by(RuleTable.insurance_type, RuleTable.effective_start.desc()).all()
    return render_template("rules.html", rules=rules)
