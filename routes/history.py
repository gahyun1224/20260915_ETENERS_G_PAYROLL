from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from decorators import admin_required
from extensions import db
from models.batch import Batch

bp = Blueprint("history", __name__)


@bp.route("/history")
@login_required
def index():
    batches = Batch.query.order_by(Batch.created_at.desc()).all()
    return render_template("history.html", batches=batches)


@bp.route("/history/<int:batch_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    db.session.delete(batch)
    db.session.commit()
    flash(f"{batch.file_name} 배치를 삭제했습니다.", "success")
    return redirect(url_for("history.index"))
