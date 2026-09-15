"""Excel 레코드 목록 -> 배치 단위 일괄 검증 -> DB 저장까지 오케스트레이션."""

import json

from extensions import db
from models.batch import Batch
from models.validation import ValidationResult
from services import evidence_service, pension_validator


def run_batch_validation(records, file_name, reference_month):
    batch = Batch(file_name=file_name, reference_month=reference_month)
    db.session.add(batch)
    db.session.flush()

    counts = {"NORMAL": 0, "ERROR": 0, "REVIEW": 0}

    for record in records:
        outcome = pension_validator.validate(record)
        evidence = evidence_service.build_evidence(outcome.get("error_code"), outcome.get("rule"))

        detail = {
            "steps": outcome["steps"],
            "message": outcome["message"],
            "evidence": _serialize_evidence(evidence),
            "np_status": record["np_status"],
            "dob": record["dob"].isoformat(),
            "age": outcome["age"],
        }

        vr = ValidationResult(
            batch_id=batch.id,
            employee_id=record["employee_id"],
            employee_name=record["name"],
            insurance_type=pension_validator.INSURANCE_TYPE,
            status=outcome["status"],
            error_code=outcome.get("error_code"),
            input_base=outcome["input_base"],
            verified_base=outcome["verified_base"],
            input_deduction=outcome["input_deduction"],
            verified_deduction=outcome["verified_deduction"],
            difference=outcome["difference"],
            detail_json=json.dumps(detail, ensure_ascii=False, default=str),
        )
        db.session.add(vr)
        counts[outcome["status"]] += 1

    batch.total_count = len(records)
    batch.normal_count = counts["NORMAL"]
    batch.error_count = counts["ERROR"]
    batch.review_count = counts["REVIEW"]
    db.session.commit()
    return batch


def _serialize_evidence(evidence):
    if not evidence:
        return None
    e = dict(evidence)
    for key in ("effective_start", "effective_end"):
        if e.get(key) is not None:
            e[key] = e[key].isoformat()
    return e
