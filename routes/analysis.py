from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from extensions import db
from models.validation import ERROR_LABELS, ValidationResult

bp = Blueprint("analysis", __name__)

CAUSE_COLORS = [
    "#b42318", "#b54708", "#175cd3", "#6941c6", "#0e9384", "#667085",
]


@bp.route("/analysis")
@login_required
def index():
    rows = (
        db.session.query(ValidationResult.error_code, func.count(ValidationResult.id))
        .filter(ValidationResult.status.in_(("ERROR", "REVIEW")))
        .group_by(ValidationResult.error_code)
        .order_by(func.count(ValidationResult.id).desc())
        .all()
    )
    total = sum(count for _, count in rows)

    causes = [
        {
            "code": code,
            "label": ERROR_LABELS.get(code, code or "-"),
            "count": count,
            "percentage": round(count / total * 100, 1) if total else 0,
            "color": CAUSE_COLORS[i % len(CAUSE_COLORS)],
        }
        for i, (code, count) in enumerate(rows)
    ]

    return render_template("analysis.html", causes=causes, total=total)
