from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from airflow.models import Variable
from airflow.decorators import task
import pendulum
import logging
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from common import check_port

KST = pendulum.timezone("Asia/Seoul")


# DAG 기본 설정
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

def _simple_py_hello():
    logging.info("simple_hello funtion run")


@task
def say_hello(name: str = "world"):
    logging.info("say_hello from task run, name : %s", name)
    
    if check_port("host.docker.internal", 3307):
        logging.info("접속 가능_ok!!!, host : %s, port : %s", "host.docker.internal", 3307)
    else:
        logging.warning("방화벽 차단 or 서비스 미동작")
        return {"greeted": name, "status": "port_unreachable"}
        

with DAG(
    dag_id="hello_world",
    default_args=default_args,
    description="",
    start_date=pendulum.datetime(2025, 9, 1, 0, 0, tz=KST),
    schedule=None, #schedule="@daily", # 매일 1회 실행
    catchup=False,
    tags=["hello"],
) as dag:
    foo_val = Variable.get("foo", default_var="bar")  # ← 기본값
    
    bash_task1 = BashOperator(
        task_id="bash_print_hello",
        bash_command=f"echo 'BashTask-Hello Airflow! foo ^^ : {foo_val}'"
    )

    bash_task2 = BashOperator(
        task_id="bash_print_date",
        bash_command="date"
    )
    
    simple_py_hello = PythonOperator(
        task_id="simple_py_hello",
        python_callable=_simple_py_hello
    )
    
    #say_hello = say_hello(name="Nice-Airflow")
    bash_task1 >> bash_task2 >> simple_py_hello >> say_hello(name="Nice-Direct-Airflow")

