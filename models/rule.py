from datetime import datetime

from extensions import db


class RuleTable(db.Model):
    """보험 항목별 요율/상하한 기준. 코드에 하드코딩하지 않고 이 테이블에서 관리한다."""

    __tablename__ = "rule_table"

    id = db.Column(db.Integer, primary_key=True)
    insurance_type = db.Column(db.String(30), nullable=False)  # 예: NATIONAL_PENSION
    rule_type = db.Column(db.String(30), nullable=False, default="STANDARD")
    effective_start = db.Column(db.Date, nullable=False)
    effective_end = db.Column(db.Date, nullable=True)  # null = 현재까지 적용중
    employee_rate = db.Column(db.Float, nullable=False)
    employer_rate = db.Column(db.Float, nullable=True)
    lower_limit = db.Column(db.Float, nullable=True)
    upper_limit = db.Column(db.Float, nullable=True)
    description = db.Column(db.String(255))
    legal_basis = db.Column(db.String(255))
    source_name = db.Column(db.String(100))
    source_url = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_current(self):
        return self.effective_end is None
