import json
from datetime import datetime

from extensions import db

STATUS_LABELS = {"NORMAL": "정상", "ERROR": "오류", "REVIEW": "추가 확인"}

ERROR_LABELS = {
    "NP_RATE_OUTDATED": "요율 적용 오류",
    "NP_CAP_NOT_APPLIED": "기준소득월액 상한 미적용",
    "NP_ELIGIBILITY_REVIEW": "가입상태 확인 필요",
    "NP_AMOUNT_MISMATCH": "공제액 불일치",
    "NP_RULE_NOT_FOUND": "적용 기준 없음",
}


class ValidationResult(db.Model):
    """직원 1명 x 보험 1종에 대한 검증 결과 (감사 목적상 수정 불가 — 재검증 시 새 배치로 재생성)."""

    __tablename__ = "validation_result"

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batch.id"), nullable=False)
    employee_id = db.Column(db.String(30), nullable=False)
    employee_name = db.Column(db.String(50), nullable=False)
    insurance_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # NORMAL / ERROR / REVIEW
    error_code = db.Column(db.String(50), nullable=True)
    input_base = db.Column(db.Float)
    verified_base = db.Column(db.Float)
    input_deduction = db.Column(db.Float)
    verified_deduction = db.Column(db.Float)
    difference = db.Column(db.Float)
    detail_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def detail(self):
        return json.loads(self.detail_json) if self.detail_json else {}

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def error_label(self):
        return ERROR_LABELS.get(self.error_code, self.error_code or "-")
