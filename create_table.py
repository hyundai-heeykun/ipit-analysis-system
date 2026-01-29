
# create_tables_ipit.py

import sqlite3

DB_PATH = "subscriptions.db"

def create_tables_ipit():
    #2)DB접속 (파일이 없으면 새로 생성됨)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    #3)테이블 생성 쿼리 실행
    create_ipit_table_sql = """
    CREATE TABLE IF NOT EXISTS subscription(
        scrbr_no      TEXT,
        status        TEXT, 
        svc_open_dh   TEXT, ---- YYYYMMdd
        rscs_dh       TEXT, ---- YYYYMMdd
        as_yn         TEXT,
        as_dh         TEXT, ---- YYYYMMdd
        ott_yn        TEXT,
        ott_prdt_nm   TEXT,
        ott_ipit_yn   TEXT,
        ott_open_dh   TEXT, ---- YYYYMMdd
        ott_rscs_dh   TEXT, ---- YYYYMMdd
        age           INTEGER,
        prdt_nm       TEXT,
        prdt_amt      INTEGER
    );
    """

    cur.execute(create_ipit_table_sql)

    #4)반영 후 닫기
    conn.commit()
    conn.close()
    print("테이블 생성 완료:",DB_PATH)

if __name__ == "__main__":
    create_tables_ipit()
