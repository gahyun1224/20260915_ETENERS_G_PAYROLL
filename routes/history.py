from flask import Blueprint, render_template
from flask_login import login_required

from models.batch import Batch

bp = Blueprint("history", __name__)


@bp.route("/history")
@login_required
def index():
    batches = Batch.query.order_by(Batch.created_at.desc()).all()
    return render_template("history.html", batches=batches)
