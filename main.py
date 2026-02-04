# -*- coding: utf-8 -*-
import sys
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

BASE_DIR = r"C:\Users\KT Skylife\PycharmProjects\ipit_status"
env_path = os.path.join(BASE_DIR, ".env")

# 환경 변수에서 프론트엔드 주소를 가져오되, 없으면 로컬 주소를 기본 값으로 사용
FRONTEND_URL = os.getenv("FRONTED_URL", "http://localhost:3000")

# 1. 반드시 파일 최상단 (또는 API설정 전)에 실행 --> .env 파일의 내용을 환경 변수로 불러옵니다.
load_dotenv(dotenv_path=env_path, override=True)

# 현재 파일(main.py)이 있는 폴더 경로를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import sqlite3

# 앞서 분리한 커스텀 모듈 임포트
from gpt_engine import ask_gpt_for_spec, generate_commentary_ipit
from db_handler import query_db_with_spec_ipit
from utils import preprocess_question, summarize_result_for_ai_ipit
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="IPIT 가입자 상태 분석 시스템 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,  # 환경 변수로 지정한 주소
        "http://127.0.0.1:3000",  # 윈도우 로컬 테스트용
        "http://localhost:3000"  # 윈도우 로컬 테스트용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 경로 설정 (환경변수 혹은 기본값)
DB_PATH = os.getenv("IPIT_DB_PATH", os.path.join(BASE_DIR, "DB", "subscriptions.db"))


# ======================
# DB 연결 의존성
# ======================
def get_db():
    """SQLite DB 연결을 생성하고 반환합니다."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail=f"DB 파일을 찾을 수 없습니다: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능하게 설정
    try:
        yield conn
    finally:
        conn.close()


# ======================
# API 요청 모델
# ======================
class AskRequest(BaseModel):
    question: str


# ======================
# 메인 비즈니스 로직 API
# ======================
@app.post("/api/ask")
def ask_api(body: AskRequest, db: sqlite3.Connection = Depends(get_db)):
    question_raw = body.question.strip()

    if not question_raw:
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    try:
        # 1) 자연어 전처리 (utils.py)
        # "올해", "작년" 등의 키워드를 분석하여 연도 힌트 추출
        processed_q, year_hint = preprocess_question(question_raw)

        # 2) GPT를 이용한 쿼리 스펙 생성 (gpt_engine.py)
        # 질문을 분석하여 metric, group_by, filters 등의 JSON 객체 반환
        spec = ask_gpt_for_spec(processed_q)

        # 전처리에서 추출된 연도 정보가 있다면 스펙에 강제 반영
        if year_hint:
            spec["year"] = year_hint

        # 3) DB 조회 및 데이터 가공 (db_handler.py)
        # 요청하신 '신규/해지/순증' 로직이 반영된 SQL 실행
        result = query_db_with_spec_ipit(spec, db)

        # 4) 분석 결과에 대한 AI 해설 생성
        # 데이터가 존재할 경우에만 요약본을 만들어 GPT에게 전달
        if result.get("table") and len(result["table"]) > 0:
            summary_text = summarize_result_for_ai_ipit(spec, result)

            # commentary = generate_commentary_ipit(question_raw, summary_text) # gpt_engine.py에서 summary param 인식 불가
            commentary = generate_commentary_ipit(question_raw, spec, summary_text)
            result["analysis"] = commentary
        else:
            result["analysis"] = "조회된 데이터가 없어 분석 내용을 생성할 수 없습니다."

        return result

    except Exception as e:
        # 실무 환경에서는 로그 파일에 상세 에러를 기록하는 것이 좋습니다.
        print(f"Error occurred: {str(e)}")
        return {
            "error": True,
            "analysis": f"처리 중 오류가 발생했습니다: {str(e)}",
            "labels": [],
            "datasets": []
        }

# src 폴더를 웹에 공개하는 설정
app.mount("/", StaticFiles(directory="src", html=True), name="static")


# ======================
# 로컬 실행 설정
# ======================
if __name__ == "__main__":
    import uvicorn

    # 내부망 서버 환경에 맞춰 host와 port 설정
    uvicorn.run(app, host="0.0.0.0", port=8000)
