
import sqlite3
import csv

DB_PATH = "subscriptions.db"
CSV_PATH = "subscription.csv"  # CSV 파일 이름/경로

def load_csv_to_db_ipit():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 기존 데이터 다 지우고 다시 넣고 싶으면 이 줄 활성화
    # cur.execute("DELETE FROM subscription")

    with open(CSV_PATH, newline='', encoding="cp949") as f:
        reader = csv.DictReader(f)

        rows = []
        for row in reader:
            rows.append((
                row["scrbr_no"],
                row["status"],
                row["svc_open_dh"],
                row.get("rscs_dh",""),
                row.get("as_yn",""),
                row.get("as_dh",""),
                row.get("ott_yn",""),
                row.get("ott_prdt_nm",""),
                row.get("ott_ipit_yn",""),
                row.get("ott_open_dh",""),
                row.get("ott_rscs_dh",""),
                row["age"],
                row["prdt_nm"],
                row["prdt_amt"]
            ))

    insert_sql = """
    INSERT INTO subscription (
        scrbr_no,
        status,
        svc_open_dh,
        rscs_dh,
        as_yn,
        as_dh,
        ott_yn,
        ott_prdt_nm,
        ott_ipit_yn,
        ott_open_dh,
        ott_rscs_dh,
        age,
        prdt_nm,
        prdt_amt
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cur.executemany(insert_sql, rows)
    conn.commit()
    conn.close()
    print(f"{len(rows)}건 CSV → DB 적재 완료")

if __name__ == "__main__":
    load_csv_to_db_ipit()

