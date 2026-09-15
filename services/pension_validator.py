"""국민연금 Rule Engine.

보험료 계산과 오류 판정은 전부 이 모듈(순수 파이썬 규칙)이 담당하며,
생성형 AI는 관여하지 않는다. Rule 수치는 하드코딩하지 않고 RuleTable에서 조회한다.

우선순위:
  1순위: 가입상태 확인 (연령 등)
  2순위: 기준소득월액 상·하한 오류
  3순위: 요율 적용 오류 (과거 요율표와 대조)
  4순위: 기타 금액 불일치
"""

import calendar
import datetime

from models.rule import RuleTable

INSURANCE_TYPE = "NATIONAL_PENSION"
AGE_REVIEW_THRESHOLD = 60
TOLERANCE = 1  # 원 단위 반올림 오차 허용


def _ref_date(reference_month):
    """'2026-08' -> 해당 월 말일(date). 월말 기준으로 연령을 계산한다."""
    year, month = (int(p) for p in reference_month.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, last_day)


def calc_age(dob, ref_date):
    return ref_date.year - dob.year - ((ref_date.month, ref_date.day) < (dob.month, dob.day))


def get_current_rule(reference_month):
    ref_date = _ref_date(reference_month)
    return (
        RuleTable.query.filter(
            RuleTable.insurance_type == INSURANCE_TYPE,
            RuleTable.effective_start <= ref_date,
        )
        .filter((RuleTable.effective_end.is_(None)) | (RuleTable.effective_end >= ref_date))
        .order_by(RuleTable.effective_start.desc())
        .first()
    )


def get_all_rules():
    return (
        RuleTable.query.filter_by(insurance_type=INSURANCE_TYPE)
        .order_by(RuleTable.effective_start.desc())
        .all()
    )


def _no_rule_result(record):
    return {
        "status": "ERROR",
        "error_code": "NP_RULE_NOT_FOUND",
        "message": "해당 기준연월에 적용할 수 있는 검증 기준이 없습니다. 기준 관리 메뉴에서 적용 기준을 확인해주세요.",
        "steps": [
            {"label": "기준연월 확인", "state": "ok"},
            {"label": "적용 기준 조회", "state": "warn"},
        ],
        "declared_income": record["np_declared_income"],
        "input_base": record["np_applied_base"],
        "verified_base": None,
        "input_deduction": record["np_deduction"],
        "verified_deduction": None,
        "difference": None,
        "age": None,
        "rule": None,
    }


def validate(record):
    """record: excel_service._row_to_record() 가 만든 dict.

    반환: dict(status, error_code, message, steps, declared_income, input_base,
               verified_base, input_deduction, verified_deduction, difference,
               age, rule)
    """
    reference_month = record["reference_month"]

    # 1) 기준연월 -> 적용 Rule 조회
    rule = get_current_rule(reference_month)
    if rule is None:
        return _no_rule_result(record)

    steps = [
        {"label": "기준연월 확인", "state": "ok"},
        {"label": f"적용 기준 조회 ({rule.effective_start} ~ {rule.effective_end or '현재'})", "state": "ok"},
    ]

    # 2) 연령 계산 및 가입조건 검토 (최우선)
    ref_date = _ref_date(reference_month)
    age = calc_age(record["dob"], ref_date)

    declared = record["np_declared_income"]
    input_base = record["np_applied_base"]
    input_deduction = record["np_deduction"]

    verified_base = max(rule.lower_limit or 0, min(rule.upper_limit or declared, declared))
    cap_applied = verified_base != declared
    verified_deduction = round(verified_base * rule.employee_rate)
    difference = input_deduction - verified_deduction

    base_result = {
        "declared_income": declared,
        "input_base": input_base,
        "verified_base": verified_base,
        "input_deduction": input_deduction,
        "verified_deduction": verified_deduction,
        "difference": difference,
        "age": age,
        "rule": rule,
    }

    if age >= AGE_REVIEW_THRESHOLD:
        steps.append({"label": f"가입조건 확인 (만 {age}세)", "state": "warn"})
        base_result.update(
            status="REVIEW",
            error_code="NP_ELIGIBILITY_REVIEW",
            message=(
                f"해당 직원은 기준일 현재 만 {age}세로, 일반적인 사업장 당연가입 연령 기준(60세)을 "
                f"초과했습니다. 현재 가입상태({record['np_status'] or '미상'})가 임의계속가입 등 "
                "별도 가입형태인지 추가 확인이 필요할 수 있습니다.\n"
                "※ 본 시스템은 자동으로 공제 오류를 확정하지 않습니다. 담당자의 최종 확인이 필요합니다."
            ),
            steps=steps,
        )
        return base_result

    steps.append({"label": "가입조건 확인", "state": "ok"})

    # 3) 기준소득월액 상·하한 확인
    steps.append(
        {
            "label": f"기준소득월액 상·하한 확인 ({rule.lower_limit:,.0f}원 ~ {rule.upper_limit:,.0f}원)",
            "state": "warn" if cap_applied else "ok",
        }
    )
    steps.append({"label": f"근로자 부담률 {rule.employee_rate * 100:g}% 적용", "state": "ok"})

    # 일치 -> 정상
    if abs(difference) <= TOLERANCE:
        steps.append({"label": "담당자 공제액과 일치", "state": "ok"})
        base_result.update(status="NORMAL", error_code=None, message="검증 기준과 입력된 공제 내역이 일치합니다.", steps=steps)
        return base_result

    # 4) 우선순위 2: 기준소득월액 상한 미적용
    if cap_applied and abs(input_base - declared) <= TOLERANCE:
        uncapped_calc = round(declared * rule.employee_rate)
        if abs(input_deduction - uncapped_calc) <= TOLERANCE:
            steps.append({"label": "기준소득월액 상한 초과 발견", "state": "warn"})
            steps.append({"label": "담당자 공제액과 불일치", "state": "warn"})
            base_result.update(
                status="ERROR",
                error_code="NP_CAP_NOT_APPLIED",
                message=(
                    f"신고소득월액({declared:,.0f}원)이 해당 기준연월의 국민연금 기준소득월액 상한액"
                    f"({rule.upper_limit:,.0f}원)을 초과하여, 담당자 적용 기준소득월액에 상한이 반영되지"
                    " 않은 것으로 확인됩니다."
                ),
                steps=steps,
            )
            return base_result

    # 5) 우선순위 3: 요율 적용 오류 (과거 요율표와 대조 — 하드코딩 금지, DB의 이력 전체와 비교)
    for old_rule in get_all_rules():
        if old_rule.id == rule.id:
            continue
        old_calc = round(verified_base * old_rule.employee_rate)
        if abs(input_deduction - old_calc) <= TOLERANCE:
            steps.append({"label": "과거 요율 적용 패턴 발견", "state": "warn"})
            steps.append({"label": "담당자 공제액과 불일치", "state": "warn"})
            base_result.update(
                status="ERROR",
                error_code="NP_RATE_OUTDATED",
                message=(
                    f"입력된 공제액은 {old_rule.effective_start} ~ {old_rule.effective_end or ''} 기간에 "
                    f"적용되던 {old_rule.employee_rate * 100:g}% 요율을 적용한 계산 결과와 일치합니다. "
                    f"{reference_month} 기준 적용 근로자 부담률({rule.employee_rate * 100:g}%)을 확인해주세요."
                ),
                steps=steps,
            )
            return base_result

    # 6) 우선순위 4: 기타 금액 불일치
    steps.append({"label": "담당자 공제액과 불일치", "state": "warn"})
    base_result.update(
        status="ERROR",
        error_code="NP_AMOUNT_MISMATCH",
        message="담당자 공제액과 시스템 검증액이 일치하지 않습니다. 알려진 오류 패턴과 일치하지 않아 담당자 확인이 필요합니다.",
        steps=steps,
    )
    return base_result
