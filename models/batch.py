from datetime import datetime

from extensions import db


class Batch(db.Model):
    """엑셀 1회 업로드 = 1개 검증 배치."""

    __tablename__ = "batch"

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    reference_month = db.Column(db.String(10), nullable=False)
    total_count = db.Column(db.Integer, default=0)
    normal_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship(
        "ValidationResult", backref="batch", order_by="ValidationResult.id", lazy=True
    )
