"""최초 실행 시 국민연금 Rule 및 기본 계정 샘플 데이터를 심는다 (프로토타입 값 — 운영 전 교체 필요)."""

from datetime import date

from extensions import db
from models.rule import RuleTable
from models.user import User
from services.pension_validator import INSURANCE_TYPE


def seed_rules():
    if RuleTable.query.filter_by(insurance_type=INSURANCE_TYPE).first():
        return

    old_rule = RuleTable(
        insurance_type=INSURANCE_TYPE,
        rule_type="STANDARD",
        effective_start=date(2025, 7, 1),
        effective_end=date(2026, 6, 30),
        employee_rate=0.045,
        employer_rate=0.045,
        lower_limit=370000,
        upper_limit=6170000,
        description="2025.07 ~ 2026.06 적용 국민연금 요율 및 기준소득월액",
        legal_basis="국민연금법 제88조, 국민연금법 시행령 제5조",
        source_name="국민연금공단",
        source_url="https://www.nps.or.kr",
    )
    current_rule = RuleTable(
        insurance_type=INSURANCE_TYPE,
        rule_type="STANDARD",
        effective_start=date(2026, 7, 1),
        effective_end=None,
        employee_rate=0.0475,
        employer_rate=0.0475,
        lower_limit=410000,
        upper_limit=6590000,
        description="2026.07 ~ 적용 국민연금 요율 및 기준소득월액",
        legal_basis="국민연금법 제88조, 국민연금법 시행령 제5조",
        source_name="국민연금공단",
        source_url="https://www.nps.or.kr",
    )
    db.session.add_all([old_rule, current_rule])
    db.session.commit()


def seed_users():
    if User.query.first():
        return

    admin = User(username="admin", name="관리자", role="admin")
    admin.set_password("admin1234")
    staff = User(username="staff1", name="김담당", role="staff")
    staff.set_password("staff1234")
    db.session.add_all([admin, staff])
    db.session.commit()
