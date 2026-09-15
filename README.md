# Payroll Guard — 페이롤 4대보험 공제 검증 AI (국민연금 MVP)

급여담당자가 직원을 한 명씩 입력·확인하는 대신, **급여 Excel 파일을 업로드하면 전체 직원을 일괄 검증하고
이상이 발견된 직원만 자동으로 선별**해 오류 유형·계산 근거·검증 과정을 보여주는 도구입니다.

이 프로그램은 보험료를 대신 계산하거나 최종 법적 판단을 내리지 않습니다. **담당자의 2차 검증을 지원하는 도구**입니다.

## 실행 방법

```bash
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

python app.py
```

실행 후 브라우저에서 http://localhost:5100 으로 접속합니다.

## 로그인

Flask-Login 기반 세션 인증이 적용되어 있습니다. 관리자만 `기준 관리`(요율 개정)에 접근할 수 있고,
나머지 메뉴(대시보드/급여 검증/검증 이력)는 담당자도 접근 가능합니다.

- 관리자: `admin` / `admin1234`
- 담당자: `staff1` / `staff1234`

## 시연 방법

1. 로그인 (위 계정 중 하나)
2. `급여 검증` 메뉴로 이동
3. `tests/fixtures/시연용_급여데이터_2026-08.xlsx` 업로드
4. 20명 중 정상 17 / 오류 2(E007, E013) / 추가확인 1(E018) 결과 확인
5. 각 직원 `상세보기`에서 검증 과정, 담당자 입력값 vs 시스템 검증값, 근거를 확인

## 테스트

```bash
pytest
```

Rule Engine 단위 테스트(`tests/test_pension.py`)와 Excel 파싱/통합 테스트(`tests/test_excel.py`, 첨부 시연용 Excel 사용)를 포함합니다.

## 아키텍처

```
Excel 업로드
  → services/excel_service.py   (파싱 · 형식 검증)
  → services/pension_validator.py (Rule Engine — 순수 계산/판정, AI 미관여)
  → services/evidence_service.py  (오류코드 → 근거 매핑; 추후 RAG 대체/보강 지점)
  → services/validation_service.py (배치 저장 오케스트레이션)
  → routes/dashboard.py, history.py, rules.py, upload.py
```

- 요율/상한액은 코드에 하드코딩하지 않고 `models/rule.py` (RuleTable)에서 관리하며, `기준 관리` 메뉴에서 새 버전을 등록할 수 있습니다.
- 국민연금 판정 우선순위: ① 가입상태(연령) 확인 → ② 기준소득월액 상·하한 → ③ 요율 적용 오류(과거 Rule 이력과 대조) → ④ 기타 금액 불일치.
- `evidence_service.build_evidence()`는 현재 RuleTable의 근거 필드를 그대로 반환하지만, 반환 dict 형태를 유지한 채
  법령 벡터DB 검색(RAG) 결과를 추가하는 방식으로 추후 확장할 수 있도록 Rule Engine과 분리되어 있습니다.

## 확장 예정

건강보험 / 장기요양보험 / 고용보험 / 소득세 등은 Excel 컬럼과 `RuleTable.insurance_type`을 추가하고,
`pension_validator.py`와 같은 형태의 개별 validator 모듈을 추가하는 방식으로 확장합니다.

## 주의사항

본 MVP는 시연용 데이터 기반으로 제작되었습니다. 실제 개인정보 및 급여정보를 업로드하지 마세요.
Rule 테이블의 요율/상한액은 프로토타입 샘플 값이며, 실제 운영 시 고시값으로 교체해야 합니다.
