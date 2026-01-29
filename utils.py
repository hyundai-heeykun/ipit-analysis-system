# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

def preprocess_question(question: str) -> Tuple[str, Optional[int]]:
    """
    질문 텍스트에서 '올해', '작년', '재작년' 등의 키워드를 찾아 
    실제 연도 숫자로 치환하고 힌트를 제공합니다.
    """
    now = datetime.now()
    now_year = now.year
    year_hint = None
    q = question

    # 키워드 기반 연도 매칭
    if "작년" in q:
        year_hint = now_year - 1
        q = q.replace("작년", f"{year_hint}년")
    elif "재작년" in q:
        year_hint = now_year - 2
        q = q.replace("재작년", f"{year_hint}년")
    elif "올해" in q or "금년" in q:
        year_hint = now_year
        q = q.replace("올해", f"{year_hint}년").replace("금년", f"{year_hint}년")
    
    # 힌트가 추출되지 않았더라도 질문에 "2024년" 처럼 명시되어 있다면 그 값을 활용하도록 함
    # (GPT가 처리할 수 있도록 질문 텍스트 자체를 정제해서 반환)
    return q, year_hint

def summarize_result_for_ai_ipit(spec: Dict[str, Any], result: Dict[str, Any]) -> str:
    """
    DB에서 가져온 차트용 데이터를 AI(GPT)가 해설하기 좋은 
    요약 텍스트 형태(Summary Report)로 변환합니다.
    """
    labels = result.get("labels", [])
    datasets = result.get("datasets", [])
    metric = spec.get("metric", "데이터")

    # 지표명에 따른 단위 설정
    is_ratio = any(kw in metric for kw in ["ratio", "rate"])
    unit = "%" if is_ratio else "명(또는 건)"

    if not labels:
        return "조회 결과 데이터가 비어 있습니다."

    summary_lines = []
    summary_lines.append(f"### [데이터 분석 요약 보고서]")
    summary_lines.append(f"- 분석 지표: {metric}")
    summary_lines.append(f"- 분석 기간: {labels[0]} ~ {labels[-1]}")
    summary_lines.append("-" * 30)

    for ds in datasets:
        group_name = ds.get("label", "전체")
        data = ds.get("data", [])
        
        if data:
            # 기본 통계량 계산
            valid_data = [v for v in data if v is not None]
            if not valid_data: continue
            
            avg_val = sum(valid_data) / len(valid_data)
            max_val = max(valid_data)
            last_val = valid_data[-1]
            
            # 소수점 처리
            fmt = ".2f" if is_ratio else ".0f"
            
            summary_lines.append(f"▶ 그룹: {group_name}")
            summary_lines.append(f"   * 평균 실적: {avg_val:{fmt}}{unit}")
            summary_lines.append(f"   * 최고 실적: {max_val:{fmt}}{unit}")
            summary_lines.append(f"   * 최근 실적({labels[-1]}): {last_val:{fmt}}{unit}")
            
            # 추세 분석 (최근 2개 시점 비교)
            if len(valid_data) >= 2:
                prev_val = valid_data[-2]
                diff = last_val - prev_val
                if diff > 0:
                    trend = f"증가 (▲{diff:{fmt}}{unit})"
                elif diff < 0:
                    trend = f"감소 (▼{abs(diff):{fmt}}{unit})"
                else:
                    trend = "변동 없음 (-)"
                summary_lines.append(f"   * 직전 대비 추세: {trend}")
            summary_lines.append("")

    return "\n".join(summary_lines)