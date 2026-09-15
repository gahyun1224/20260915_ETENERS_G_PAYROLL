"""급여 데이터 Excel 업로드 파싱.

담당자가 올린 .xlsx 파일을 읽어 직원별 dict 리스트로 변환한다.
계산이나 판정은 하지 않고, 오직 파싱/형식 검증만 담당한다.
"""

import pandas as pd

REQUIRED_COLUMNS = [
    "사번",
    "성명",
    "생년월일",
    "기준연월",
    "국민연금 가입상태",
    "국민연금 신고소득월액",
    "담당자 적용 기준소득월액",
    "국민연금 공제액",
]

OPTIONAL_COLUMNS = [
    "입사일",
    "퇴사일",
    "건강보험 보수월액",
    "건강보험 공제액",
    "장기요양보험 공제액",
    "고용보험 보수월액",
    "고용보험 공제액",
]

PREFERRED_SHEET_NAME = "급여데이터"


class ExcelValidationError(Exception):
    """파일 자체를 읽을 수 없거나 필수 컬럼이 없는 등, 배치 전체를 중단해야 하는 오류."""

    def __init__(self, message, missing_columns=None):
        super().__init__(message)
        self.missing_columns = missing_columns or []


def load_payroll_excel(file_stream, filename=""):
    """반환: (records, row_errors)

    records: 정상 파싱된 직원 dict 리스트
    row_errors: 개별 행 파싱 실패 메시지 리스트 (배치 자체는 중단되지 않음)
    """
    if not filename.lower().endswith(".xlsx"):
        raise ExcelValidationError("지원하지 않는 파일 형식입니다.\n.xlsx 파일을 업로드해주세요.")

    try:
        xls = pd.ExcelFile(file_stream, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        raise ExcelValidationError(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {exc}")

    sheet_name = PREFERRED_SHEET_NAME if PREFERRED_SHEET_NAME in xls.sheet_names else xls.sheet_names[0]

    try:
        df = xls.parse(sheet_name)
    except Exception as exc:  # noqa: BLE001
        raise ExcelValidationError(f"시트를 읽는 중 오류가 발생했습니다: {exc}")

    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ExcelValidationError(
            "필수 컬럼을 찾을 수 없습니다.\n\n누락 컬럼:\n" + "\n".join(f"- {c}" for c in missing),
            missing_columns=missing,
        )

    df = df.dropna(how="all")

    records = []
    row_errors = []
    for i, row in df.iterrows():
        excel_row_no = i + 2  # 1행은 헤더
        try:
            records.append(_row_to_record(row))
        except Exception as exc:  # noqa: BLE001
            emp_ref = _safe_str(row.get("사번")) or f"{excel_row_no}행"
            row_errors.append(f"{emp_ref} 직원의 데이터 형식을 확인해주세요: {exc}")

    return records, row_errors


def _safe_str(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _to_float(row, col, default=0.0):
    value = row.get(col)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return float(value)


def _to_date(row, col):
    value = row.get(col)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if hasattr(value, "date"):
        return value.date()
    return pd.to_datetime(value).date()


def _row_to_record(row):
    employee_id = _safe_str(row.get("사번"))
    if not employee_id:
        raise ValueError("사번이 비어있습니다.")

    name = _safe_str(row.get("성명")) or ""

    dob = _to_date(row, "생년월일")
    if dob is None:
        raise ValueError("생년월일 형식을 확인해주세요.")

    reference_month = _safe_str(row.get("기준연월"))
    if not reference_month:
        raise ValueError("기준연월이 비어있습니다.")

    return {
        "employee_id": employee_id,
        "name": name,
        "dob": dob,
        "reference_month": reference_month,
        "hire_date": _to_date(row, "입사일"),
        "resign_date": _to_date(row, "퇴사일"),
        "np_status": _safe_str(row.get("국민연금 가입상태")) or "",
        "np_declared_income": _to_float(row, "국민연금 신고소득월액"),
        "np_applied_base": _to_float(row, "담당자 적용 기준소득월액"),
        "np_deduction": _to_float(row, "국민연금 공제액"),
        "hi_base": _to_float(row, "건강보험 보수월액", None),
        "hi_deduction": _to_float(row, "건강보험 공제액", None),
        "ltc_deduction": _to_float(row, "장기요양보험 공제액", None),
        "ei_base": _to_float(row, "고용보험 보수월액", None),
        "ei_deduction": _to_float(row, "고용보험 공제액", None),
    }
