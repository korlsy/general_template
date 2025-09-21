# dags/example_python_operator.py
from datetime import timedelta
import logging

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
import mysql.connector

def check_port(ip, port, timeout=3):
    import socket
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception as e:
        return False

def hello(name: str = "world", **context):
    logging.info("begin hello, %s!", "first")
    
    if check_port("host.docker.internal", 3307):
        logging.info("접속 가능_ok!!!")
    else:
        logging.info("방화벽 차단 or 서비스 미동작")

    logging.info("mysql_connect_using_direct")
    
    conn = mysql.connector.connect(
        host="host.docker.internal",
        port=3307,
        user="lsy",
        password="lsy",
        database="lsy",
    )
    logging.info("conn : %s", conn)
    return {"greeted": name}

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
        python_callable=hello,
        op_kwargs={"name": "Nice-Airflow"},
    )
    say_hello
