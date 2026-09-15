import io
import os

import pytest
from openpyxl import Workbook

from services import excel_service, validation_service

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "시연용_급여데이터_2026-08.xlsx")


def _build_minimal_workbook(rows, headers):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def test_missing_excel_column():
    headers = ["사번", "성명", "생년월일"]  # 기준연월 등 필수 컬럼 누락
    buf = _build_minimal_workbook([["E001", "홍길동", "1990-01-01"]], headers)

    with pytest.raises(excel_service.ExcelValidationError) as exc_info:
        excel_service.load_payroll_excel(buf, "test.xlsx")

    assert "필수 컬럼" in str(exc_info.value)
    assert "국민연금 공제액" in exc_info.value.missing_columns


def test_rejects_non_xlsx():
    buf = io.BytesIO(b"not an excel file")
    with pytest.raises(excel_service.ExcelValidationError):
        excel_service.load_payroll_excel(buf, "test.csv")


def test_bad_row_is_skipped_not_crashed():
    headers = [
        "사번", "성명", "생년월일", "기준연월", "국민연금 가입상태",
        "국민연금 신고소득월액", "담당자 적용 기준소득월액", "국민연금 공제액",
    ]
    rows = [
        ["E001", "정상직원", "1990-01-01", "2026-08", "사업장가입자", 3000000, 3000000, 142500],
        [None, "사번없음", "1990-01-01", "2026-08", "사업장가입자", 3000000, 3000000, 142500],
    ]
    buf = _build_minimal_workbook(rows, headers)
    records, row_errors = excel_service.load_payroll_excel(buf, "test.xlsx")

    assert len(records) == 1
    assert len(row_errors) == 1


def test_demo_excel_integration(app):
    """첨부된 시연용 Excel을 실제로 업로드했을 때 지시서에 명시된 결과가 나와야 한다."""
    with open(FIXTURE_PATH, "rb") as f:
        records, row_errors = excel_service.load_payroll_excel(f, os.path.basename(FIXTURE_PATH))

    assert row_errors == []
    assert len(records) == 20

    batch = validation_service.run_batch_validation(
        records, os.path.basename(FIXTURE_PATH), records[0]["reference_month"]
    )

    assert batch.total_count == 20
    assert batch.normal_count == 17
    assert batch.error_count == 2
    assert batch.review_count == 1

    by_id = {r.employee_id: r for r in batch.results}
    assert by_id["E007"].status == "ERROR"
    assert by_id["E007"].error_code == "NP_RATE_OUTDATED"
    assert by_id["E013"].status == "ERROR"
    assert by_id["E013"].error_code == "NP_CAP_NOT_APPLIED"
    assert by_id["E018"].status == "REVIEW"
    assert by_id["E018"].error_code == "NP_ELIGIBILITY_REVIEW"

    normal_ids = {"E001", "E002", "E003", "E004", "E005", "E006", "E008", "E009", "E010",
                  "E011", "E012", "E014", "E015", "E016", "E017", "E019", "E020"}
    for emp_id in normal_ids:
        assert by_id[emp_id].status == "NORMAL", f"{emp_id} expected NORMAL"
