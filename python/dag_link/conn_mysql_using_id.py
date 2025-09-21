from datetime import timedelta
import logging

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from lib.common import check_port

CONN_ID = "airflow_mysql_db" 
    
def mysql_job(name: str = "world", **context):
    logging.info("begin hello, %s!", name)

    if check_port("host.docker.internal", 3307):
        logging.info("접속 가능_ok!!!")
    else:
        logging.warning("방화벽 차단 or 서비스 미동작")
        return {"greeted": name, "status": "port_unreachable"}

    hook = MySqlHook(mysql_conn_id=CONN_ID)
    logging.info("hook: %s", hook)

    inserted_id = None
    try:
        with hook.get_conn() as conn:
            with conn.cursor() as cur:
                # 0) 테이블 없으면 생성
                cur.execute("""
                CREATE TABLE IF NOT EXISTS sample_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    value INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                conn.commit()
                logging.info("sample_table 확인(없으면 생성) 완료")

                # 1) INSERT
                cur.execute(
                    "INSERT INTO sample_table (name, value) VALUES (%s, %s)",
                    (name, 123)
                )
                conn.commit()
                inserted_id = cur.lastrowid
                logging.info("INSERT 완료, inserted_id=%s", inserted_id)

                # 2) SELECT - 방금 넣은 row 조회
                cur.execute(
                    "SELECT id, name, value, created_at FROM sample_table WHERE id = %s",
                    (inserted_id,)
                )
                row = cur.fetchone()
                if row:
                    logging.info("방금 추가된 행: %s", row)
                else:
                    logging.warning("방금 추가한 행을 찾을 수 없음. id=%s", inserted_id)

                # 최근 5개 확인
                cur.execute("""
                    SELECT id, name, value, created_at 
                    FROM sample_table 
                    ORDER BY id DESC LIMIT 5
                """)
                recent_rows = cur.fetchall()
                logging.info("최근 5개 행:")
                for r in recent_rows:
                    logging.info("  %s", r)

    except Exception as e:
        logging.error("MySQL 작업 오류: %s", e)
        return {"greeted": name, "status": "error", "error": str(e)}

    return {"param.name": name, "status": "ok", "inserted_id": inserted_id}


with DAG(
    dag_id="conn_mysql_using_id",
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

    job_mysql = PythonOperator(
        task_id="job_mysql",
        python_callable=mysql_job,
        op_kwargs={"name": "Nice-Airflow"},
    )

    job_mysql

