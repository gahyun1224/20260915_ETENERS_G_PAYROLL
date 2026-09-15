from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from services import excel_service, validation_service

bp = Blueprint("upload", __name__)


@bp.route("/upload", methods=["GET"])
@login_required
def upload_form():
    return render_template("upload.html")


@bp.route("/upload", methods=["POST"])
@login_required
def upload_submit():
    file = request.files.get("payroll_file")
    if not file or file.filename == "":
        flash("업로드할 엑셀 파일을 선택해주세요.", "danger")
        return redirect(url_for("upload.upload_form"))

    try:
        records, row_errors = excel_service.load_payroll_excel(file.stream, file.filename)
    except excel_service.ExcelValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("upload.upload_form"))
    except Exception as exc:  # noqa: BLE001 — 업로드 파이프라인은 절대 죽지 않아야 한다
        flash(f"파일 처리 중 예기치 못한 오류가 발생했습니다: {exc}", "danger")
        return redirect(url_for("upload.upload_form"))

    if not records:
        flash("업로드한 파일에서 유효한 직원 데이터를 찾지 못했습니다.", "danger")
        for msg in row_errors:
            flash(msg, "warning")
        return redirect(url_for("upload.upload_form"))

    reference_month = records[0]["reference_month"]

    try:
        batch = validation_service.run_batch_validation(records, file.filename, reference_month)
    except Exception as exc:  # noqa: BLE001
        flash(f"검증 처리 중 오류가 발생했습니다: {exc}", "danger")
        return redirect(url_for("upload.upload_form"))

    for msg in row_errors:
        flash(msg, "warning")
    flash(f"{len(records)}명의 직원 데이터 검증이 완료되었습니다.", "success")

    return redirect(url_for("dashboard.view_batch", batch_id=batch.id))
