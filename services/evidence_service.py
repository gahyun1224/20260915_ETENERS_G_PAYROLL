"""오류 코드와 근거(조문/고시/기준)를 연결하는 모듈. Rule Engine과 분리되어 있다.

현재는 RuleTable에 저장된 legal_basis/source 정보를 그대로 반환하지만,
추후 RAG(법령 벡터DB 검색 + LLM 요약) 모듈로 이 함수를 교체하거나 보강할 수 있도록
반환 형태(dict)를 안정적인 인터페이스로 유지한다.
  예) build_evidence()가 반환하는 dict에 rag_snippets 필드를 추가하는 방식으로 확장
"""

EVIDENCE_CATEGORY = {
    "NP_RATE_OUTDATED": "해당 기준연월 국민연금 보험료율",
    "NP_CAP_NOT_APPLIED": "해당 기준연월 기준소득월액 상한",
    "NP_ELIGIBILITY_REVIEW": "사업장가입자 연령 관련 기준",
    "NP_AMOUNT_MISMATCH": "국민연금 보험료 산정 기준",
    "NP_RULE_NOT_FOUND": "국민연금 요율/기준소득월액 기준",
}


def build_evidence(error_code, rule):
    """error_code + 적용된 RuleTable row -> 근거 dict. rule이 없으면 None."""
    if rule is None:
        return None

    return {
        "category": EVIDENCE_CATEGORY.get(error_code, "관련 기준"),
        "employee_rate": rule.employee_rate,
        "lower_limit": rule.lower_limit,
        "upper_limit": rule.upper_limit,
        "effective_start": rule.effective_start,
        "effective_end": rule.effective_end,
        "legal_basis": rule.legal_basis,
        "source_name": rule.source_name,
        "source_url": rule.source_url,
        "description": rule.description,
    }
