# gpt_engine.py
import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client: Optional[OpenAI] = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

def ask_gpt_for_spec(question: str) -> Dict[str, Any]:
    if client is None:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    # 기존 시스템 프롬프트 내용 유지
    system_prompt = """
    
너는 IPIT 서비스(subscription 테이블)를 분석하는 데이터 분석 도우미이다.
사용자의 자연어 질문을 아래 JSON 스펙 1개로 변환한다.

⚠️ 매우 중요:
- 반드시 JSON 객체 1개만 출력한다.
- 설명, 문장, 코드블록(````json`)은 절대 출력하지 않는다.


=====================
[지표(metric) 정의 규칙] - 중요
=====================
1. 가입자 수 관련:
   - 신규 가입: "new_cnt"
   - 해지 건수: "cancel_cnt"
   - 순증(가입-해지): "growth_cnt"
   - 특정 시점 재적/가입 고객수: "ott_join_cnt"

2. 비율(Ratio/Rate) 관련:
   - OTT 가입률/비중: "ott_ratio" (전체 대비 OTT 가입자 비율)
   - AS 발생률/비중: "as_ratio" (조회 대상 중 AS 발생 고객 비율)
   - 일반 상품 비중: "prdt_ratio" (전체 중 특정 prdt_nm이 차지하는 비율)
   - OTT 상품 비중: "ott_prdt_ratio" (전체 중 특정 ott_prdt_nm이 차지하는 비율)


=====================
[JSON 스펙 스키마]
=====================

{
  "metric": "new_cnt" | "cancel_cnt" | "growth_cnt" | "ott_join_cnt" | "ott_ratio",
  "time_grain": "year" | "month" | "day",
  "year": number | null,
  "month": "YYYYMM" | null,
  "day": "YYYYMMDD" | null,
  "group_by": "none" | "status" | "as_yn" | "ott_prdt_nm" | "prdt_nm" | "age_band" | "prdt_amt_band",
  "chart_type": "line" | "bar" | "pie",
  "filters": {
    "status": string | null,
    "as_yn": "Y" | "N" | null,
    "ott_prdt_nm": string | null,
    "ott_open_dh": "YYYY|YYYYMM|YYYYMMDD" | null,
    "as_dh": "YYYY|YYYYMM|YYYYMMDD" | null,
    "prdt_nm": string | null,
    "age_eq": number | null,
    "age_min": number | null,
    "age_max": number | null,
    "prdt_amt_eq": number | null,
    "prdt_amt_min": number | null,
    "prdt_amt_max": number | null
  }
}

=====================
[작성 규칙]
=====================

1) 기간
- 기간 미언급 시 time_grain="month"
- year/month/day 중 하나만 채운다

2) 지표(metric)
2-1) 가입자 수 관련:
- 신규: new_cnt
- 해지: cancel_cnt
- 순증: growth_cnt
- OTT 가입: ott_join_cnt

2-2) 비율(Ratio/Rate0 관련: 
- OTT 가입률/비중: "ott_ratio" (전체 대비 OTT 가입자 비율)
- OTT 상품 비중: "ott_prdt_ratio" (전체 중 특정 ott_prdt_nm이 차지하는 비율)
- 일반 상품 비중: "prdt_ratio" (전체 중 특정 prdt_nm이 차지하는 비율)
- AS 발생률/비중: "as_ratio" (조회 대상 중 AS 발생 고객 비율)

3) 필터(filters)
- filters 안의 모든 조건은 AND 조건이다
- 언급되지 않은 필드는 null로 둔다

4) group_by
- "~별" 표현이 있으면 해당 값 사용
- 없으면 "none"

5) chart_type
- 시계열이면 line
- 분류 비교면 bar
- 비율/구성 요청이면 pie 


=====================
[작성 가이드]
=====================
- "비율", "비중", "발생률" 단어가 포함되면 반드시 Ratio 관련 지표를 선택한다.
- "30대" 요청 시: age_min=30, age_max=39 설정.
- "2만원 이상" 요청 시: prdt_amt_min=20000 설정.
- 특정 상품 언급 시: 해당 상품명을 filters의 prdt_nm 또는 ott_prdt_nm에 기입한다.   
    """
    
    user_prompt = f"질문: {question}\n위 형식의 JSON 객체만 반환해."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    content = (response.choices[0].message.content or "").strip()
    print("GPT raw spec:", content)

    try:
        spec = json.loads(content)
    except json.JSONDecodeError as e:
        print("JSON 파싱 오류:", e)
        raise RuntimeError("GPT 응답을 JSON으로 파싱할 수 없습니다.")

    return json.loads(content)

def generate_commentary_ipit(question: str, spec: Dict[str, Any], summary: str) -> str:
    """
    요약된 데이터와 사용자 질문을 바탕으로 GPT가 최종 해설을 생성합니다.
    """
    if client is None:
        return "OpenAI API 키가 설정되지 않아 해설을 생성할 수 없습니다."

    system_prompt = "너는 통신 서비스 데이터 분석 전문가이다. 제공된 데이터 요약본을 바탕으로 사용자의 질문에 친절하고 통찰력 있게 답변하라."
    user_prompt = f"질문: {question}\n\n데이터 요약:\n{summary}\n\n위 데이터를 바탕으로 분석 결과의 특징과 의미를 2~3문장으로 요약해서 설명해줘."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"해설 생성 중 오류가 발생했습니다: {str(e)}"