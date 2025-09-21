# dags/example_python_operator.py
from datetime import timedelta
import logging

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
import mysql.connector
from lib.common import check_port


def mysql_job(name: str = "mysql_world", **context):
    logging.info("begin mysql_job, %s", name)

    if not check_port("host.docker.internal", 3307):
        logging.info("방화벽 차단 or 서비스 미동작 (host.docker.internal:3307)")
        return {"param.name": name, "status": "port_unreachable"}

    logging.info("mysql_connect_using_direct")

    conn = None
    cursor = None
    inserted_id = None

    try:
        conn = mysql.connector.connect(
            host="host.docker.internal",
            port=3307,
            user="lsy",
            password="lsy",
            database="lsy",
            # auth_plugin="mysql_native_password"  # 필요시 주석 해제
        )
        logging.info("conn: %s", conn.is_connected())

        cursor = conn.cursor()

        # 0) 테이블이 없으면 생성
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS sample_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            value INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_table_sql)
        # DDL은 대부분 자동 커밋이지만 안전하게 commit 호출
        conn.commit()
        logging.info("sample_table 확인(없으면 생성) 완료")

        # 1) INSERT 예제 - 파라미터 바인딩으로 안전하게
        insert_sql = "INSERT INTO sample_table (name, value) VALUES (%s, %s)"
        insert_params = (name, 123)
        cursor.execute(insert_sql, insert_params)
        conn.commit()  # 반드시 커밋
        inserted_id = cursor.lastrowid
        logging.info("INSERT 완료, inserted_id=%s", inserted_id)

        # 2) SELECT 예제 - 방금 넣은 row만 조회
        select_sql = "SELECT id, name, value, created_at FROM sample_table WHERE id = %s"
        cursor.execute(select_sql, (inserted_id,))
        row = cursor.fetchone()
        if row:
            logging.info("방금 추가된 행: id=%s, name=%s, value=%s, created_at=%s",
                         row[0], row[1], row[2], row[3])
        else:
            logging.warning("방금 추가한 행을 찾을 수 없습니다. id=%s", inserted_id)

        # 추가: 최근 5개 행을 확인하고 싶으면
        cursor.execute("SELECT id, name, value, created_at FROM sample_table ORDER BY id DESC LIMIT 5")
        recent_rows = cursor.fetchall()
        logging.info("최근 5개 행:")
        for r in recent_rows:
            logging.info("  %s", r)

    except Error as e:
        logging.error("MySQL 에러: %s", e)
        return {"param.name": name, "status": "error", "error": str(e)}
    except Exception as e:
        logging.error("예상치 못한 에러: %s", e)
        return {"param.name": name, "status": "error", "error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
        logging.info("MySQL 연결 종료")

    return {"param.name": name, "status": "ok", "inserted_id": inserted_id}
with DAG(
    dag_id="conn_mysql_using_direct",
    description="",
    start_date=pendulum.datetime(2025, 9, 1, tz="Asia/Seoul"),
    schedule="@daily",
    catchup=False,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=3),
    },
    tags=["mysql_connection_test"],
) as dag:
    say_hello = PythonOperator(
        task_id="say_hello",
        python_callable=mysql_job,
        op_kwargs={"name": "mysql_db"},
    )
    say_hello
