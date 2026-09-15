import datetime

from services import pension_validator

REFERENCE_MONTH = "2026-08"


def _record(**overrides):
    base = {
        "employee_id": "T001",
        "name": "테스트",
        "dob": datetime.date(1994, 3, 12),
        "reference_month": REFERENCE_MONTH,
        "np_status": "사업장가입자",
        "np_declared_income": 3000000,
        "np_applied_base": 3000000,
        "np_deduction": 142500,  # 3,000,000 * 4.75%
    }
    base.update(overrides)
    return base


def test_normal_employee(app):
    result = pension_validator.validate(_record())
    assert result["status"] == "NORMAL"
    assert result["error_code"] is None
    assert result["difference"] == 0


def test_outdated_rate(app):
    # 4.5%(구 요율)로 계산한 공제액을 그대로 입력한 경우
    record = _record(np_declared_income=3000000, np_applied_base=3000000, np_deduction=135000)
    result = pension_validator.validate(record)
    assert result["status"] == "ERROR"
    assert result["error_code"] == "NP_RATE_OUTDATED"


def test_cap_not_applied(app):
    # 신고소득월액이 상한을 초과하는데 상한을 적용하지 않고 계산한 경우
    record = _record(
        np_declared_income=10000000,
        np_applied_base=10000000,
        np_deduction=475000,  # 10,000,000 * 4.75% (상한 미적용)
    )
    result = pension_validator.validate(record)
    assert result["status"] == "ERROR"
    assert result["error_code"] == "NP_CAP_NOT_APPLIED"
    assert result["verified_base"] == 6590000
    assert result["verified_deduction"] == round(6590000 * 0.0475)


def test_eligibility_review(app):
    # 기준일 현재 만 60세 이상 + 공제액 자체는 정확히 계산된 경우에도 REVIEW로 분류되어야 한다
    record = _record(
        dob=datetime.date(1965, 5, 15),
        np_declared_income=4000000,
        np_applied_base=4000000,
        np_deduction=190000,  # 4,000,000 * 4.75% (금액 자체는 정확)
    )
    result = pension_validator.validate(record)
    assert result["status"] == "REVIEW"
    assert result["error_code"] == "NP_ELIGIBILITY_REVIEW"
    # 금액이 맞더라도 확정 오류 판정(공제액=0 등)을 내려서는 안 된다
    assert "확정하지 않습니다" in result["message"]


def test_unknown_amount_mismatch(app):
    # 과거 요율/상한 미적용 어느 패턴에도 맞지 않는 임의의 불일치
    record = _record(np_declared_income=3000000, np_applied_base=3000000, np_deduction=999999)
    result = pension_validator.validate(record)
    assert result["status"] == "ERROR"
    assert result["error_code"] == "NP_AMOUNT_MISMATCH"


def test_no_hardcoded_employee_id(app):
    """E007이 아닌 다른 사번이라도 동일한 금액 패턴이면 동일하게 탐지되어야 한다 (하드코딩 금지 검증)."""
    record = _record(employee_id="Z999", np_declared_income=3000000, np_applied_base=3000000, np_deduction=135000)
    result = pension_validator.validate(record)
    assert result["error_code"] == "NP_RATE_OUTDATED"
