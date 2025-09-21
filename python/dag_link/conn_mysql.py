# dags/example_python_operator.py
from datetime import timedelta
import logging

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

from airflow.providers.mysql.hooks.mysql import MySqlHook

CONN_ID = "airflow_mysql_db" 

def check_port(ip, port, timeout=3):
    import socket
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception as e:
        return False
    

def hello(name: str = "world", **context):

    if check_port("host.docker.internal", 3307):
        print("접속 가능_ok!!!")
    else:
        print("방화벽 차단 or 서비스 미동작")

        
    hook = MySqlHook(mysql_conn_id=CONN_ID)
    print("hook", hook)

    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            #cur.execute("USE gaiadb")
            cur.execute("SELECT 1")
            result = cur.fetchone()
            print(f"SELECT 1 결과: {result}")

            # 4) 데이터베이스 목록 확인
            cur.execute("SHOW TABLES")
            tables = cur.fetchall()
            print(f"테이블 목록: {tables}")

            return {
                "select_1": result,
                "tables": tables
            }


    logging.info("👋 Hello, %s!", name)
    # XCom 예시: return 값은 자동으로 XCom으로 저장됩니다.
    return {"greeted": name}

with DAG(
    dag_id="conn_mysql",
    description="가장 단순한 PythonOperator 예제",
    start_date=pendulum.datetime(2025, 9, 1, tz="Asia/Seoul"),
    schedule="@daily",
    catchup=False,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=3),
    },
    tags=["example", "pythonoperator"],
) as dag:

    say_hello = PythonOperator(
        task_id="say_hello",
        python_callable=hello,
        op_kwargs={"name": "Airflow"},
    )

    say_hello

