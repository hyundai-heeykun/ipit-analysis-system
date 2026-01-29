# db_handler.py
import sqlite3
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

def period_expr(date_col: str, time_grain: str) -> str:
    """DB의 YYYYMMDD 텍스트 날짜를 분석 단위에 맞춰 변환"""
    if time_grain == "year": 
        return f"substr({date_col}, 1, 4)"
    if time_grain == "day": 
        return f"substr({date_col}, 1, 4) || '-' || substr({date_col}, 5, 2) || '-' || substr({date_col}, 7, 2)"
    return f"substr({date_col}, 1, 4) || '-' || substr({date_col}, 5, 2)"


def group_expr(group_by: str) -> Optional[str]:
    """
    GPT가 판단한 그룹화 기준(연령대, 상품명 등)을 SQL 표현식으로 변환합니다.
    """
    if not group_by or group_by == "none": 
        return None

    # 1:1 매칭 컬럼
    if group_by in ("status", "as_yn", "ott_prdt_nm", "prdt_nm"): 
        return group_by

    # 연령대 구간 (10대, 20대...)
    if group_by == "age_band": 
        return "(CAST(NULLIF(age,'') AS INTEGER)/10)*10 || '대'"

    # 가격대 구간 (10,000원대~)
    if group_by == "prdt_amt_band": 
        return "((CAST(NULLIF(prdt_amt,'') AS INTEGER)/10000)*10000) || '원대'"

    return None


def build_where_from_filters(filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    필터 조건을 SQL WHERE 절과 파라미터 딕셔너리로 변환합니다. (SQL Injection 방지)
    """
    where_sql = " WHERE 1=1 "
    params = {}
    if not filters: 
        return where_sql, params

    # 1. 문자열 필터 (부분 일치 LIKE 적용)
    for key in ("status", "ott_prdt_nm", "prdt_nm"):
        val = filters.get(key)
        if val:
            where_sql += f" AND {key} LIKE :{key}"
            params[key] = f"%{str(val).strip()}%"

    # 2. 수치형 범위 필터 (예시: 30대 -> 30~39세 / 2만원 이상 -> 20,000원 보다 큰 금액)
    if filters.get("age_min") is not None:
        where_sql += " AND age >= :age_min"
        params["age_min"] = filters["age_min"]
    if filters.get("age_max") is not None:
        where_sql += " AND age <= :age_max"
        params["age_max"] = filters["age_max"]
    if filters.get("prdt_amt_min") is not None:
        where_sql += " AND prdt_amt >= :prdt_amt_min"
        params["prdt_amt_min"] = filters["prdt_amt_min"]

    # 3. 여부 필터
    if filters.get("as_yn"):
        where_sql += " AND as_yn = :as_yn"
        params["as_yn"] = str(filters["as_yn"]).upper()

    return where_sql, params

#
def query_db_with_spec_ipit(spec: Dict[str, Any], db: sqlite3.Connection) -> Dict[str, Any]:
    """
    GPT 스펙을 바탕으로 요청하신 신규/해지/순증 로직을 적용하여 쿼리하고 결과를 반환합니다.
    """
    metric = spec.get("metric", "new_cnt")
    time_grain = spec.get("time_grain", "month")
    group_by = spec.get("group_by", "none")
    filters = spec.get("filters", {})

    # 날짜 포맷팅 정의 (YYYY-MM 형태)
    date_fmt = "substr({col}, 1, 4) || '-' || substr({col}, 5, 2)"

    # 지표별 핵심 로직
    # 1. 일반 상품 관련
    if metric in ["new_cnt", "cancel_cnt", "growth_cnt"]:
        # 기준 날짜: svc_open_dh(개통), rscs_dh(해지)
        p_col = "svc_open_dh" if metric != "cancel_cnt" else "rscs_dh"
        # 신규 조건 : 개통월=기준월 AND 해지월!=기준월
        new_cond = f"({date_fmt.format(col='svc_open_dh')} = {date_fmt.format(col=p_col)} AND {date_fmt.format(col='rscs_dh')} != {date_fmt.format(col=p_col)})"
        # 해지 조건 : 해지월=기준월 AND 개통월!=기준월
        can_cond = f"({date_fmt.format(col='rscs_dh')} = {date_fmt.format(col=p_col)} AND {date_fmt.format(col='svc_open_dh')} != {date_fmt.format(col=p_col)})"

        if metric == "new_cnt":
            val_expr = f"COUNT(CASE WHEN {new_cond} THEN scrbr_no END)"
        elif metric == "cancel_cnt":
            val_expr = f"COUNT(CASE WHEN {can_cond} THEN scrbr_no END)"
        else:  # growth_cnt (순증)
            val_expr = f"COUNT(CASE WHEN {new_cond} THEN scrbr_no END) - COUNT(CASE WHEN {can_cond} THEN scrbr_no END)"

    # 2. OTT 상품 관련
    elif metric in ["ott_new_cnt", "ott_cancel_cnt", "ott_growth_cnt"]:
        # 기준 날짜: ott_open_dh(개통), ott_rscs_dh(해지)
        p_col = "ott_open_dh" if metric != "ott_cancel_cnt" else "ott_rscs_dh"
        # ott 신규 : ott_open_dh와 기준월이 같고 (전체해지나 ott해지 중 하나라도 기준월과 다름)
        ott_new_cond = f"({date_fmt.format(col='ott_open_dh')} = {date_fmt.format(col=p_col)} AND ({date_fmt.format(col='rscs_dh')} != {date_fmt.format(col=p_col)} OR {date_fmt.format(col='ott_rscs_dh')} != {date_fmt.format(col=p_col)}))"
        # ott 해지 : ott_rscs_dh와 기준월이 같고 (ott개통이나 전체개통 중 하나라도 기준월과 다름)
        ott_can_cond = f"({date_fmt.format(col='ott_rscs_dh')} = {date_fmt.format(col=p_col)} AND ({date_fmt.format(col='ott_open_dh')} != {date_fmt.format(col=p_col)} OR {date_fmt.format(col='svc_open_dh')} != {date_fmt.format(col=p_col)}))"

        if metric == "ott_new_cnt":
            val_expr = f"COUNT(CASE WHEN {ott_new_cond} THEN scrbr_no END)"
        elif metric == "ott_cancel_cnt":
            val_expr = f"COUNT(CASE WHEN {ott_can_cond} THEN scrbr_no END)"
        else:  # ott_growth_cnt
            val_expr = f"COUNT(CASE WHEN {ott_new_cond} THEN scrbr_no END) - COUNT(CASE WHEN {ott_can_cond} THEN scrbr_no END)"
    # 3. 기타 예외 처리
    else:
        # 기본 처리
        val_expr = "COUNT(scrbr_no)"
        p_col = "svc_open_dh"

    # --- [SQL 쿼리 조립] ---
    time_label = period_expr(p_col, time_grain)
    where_sql, params = build_where_from_filters(filters)
    g_col = group_expr(group_by)

    if g_col:
        sql = f"SELECT {time_label} as period, {g_col} as grp, {val_expr} as val FROM subscription {where_sql} GROUP BY period, grp ORDER BY period"
    else:
        sql = f"SELECT {time_label} as period, 'Total' as grp, {val_expr} as val FROM subscription {where_sql} GROUP BY period ORDER BY period"


    # --- [실행 및 결과 가공] ---
    cur = db.execute(sql, params)
    rows = cur.fetchall()

    # Chart.js가 이해할 수 있는 구조로 변환
    periods = sorted(list(set(r['period'] for r in rows)))
    groups = sorted(list(set(r['grp'] for r in rows)))

    datasets = []

    for g in groups:
        data_points = []
        for p in periods:
            # 해당 기간/그룹에 맞는 값을 찾고 없으면 0
            val = next((r['val'] for r in rows if r['period'] == p and r['grp'] == g), 0)
            data_points.append(val)
        datasets.append({"label": str(g), "data": data_points})

    return {
        "chart_type": spec.get("chart_type", "line"),
        "labels": periods,
        "datasets": datasets,
        "table": [dict(r) for r in rows] # 표 형식 데이터 병행 제공
    }