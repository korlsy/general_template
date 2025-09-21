from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from datetime import datetime, timedelta
from airflow.models import Variable
from airflow.decorators import task

import logging

# DAG 기본 설정
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

def simple_hello():
    logging.info("simple_hello funtion run")
    
@task
def say_hello(name: str = "world"):
    logging.info("say_hello from task run, name : %s", name)
    
with DAG(
    dag_id="hello_world",
    default_args=default_args,
    description="A simple Hello World DAG",
    schedule_interval="@daily",   # 매일 1회 실행
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["hello"],
) as dag:
    logging.info("begin hello, name : %s", "foo")
    
    # 변수 읽기
    #foo_val = Variable.get("foo")   # UI에서 만든 key=foo 값("bar") 불러오기
    foo_val = Variable.get("foo", default_var="bar")  # ← 기본값

    t1 = BashOperator(
        task_id="print_hello",
        bash_command=f"echo 'Hello Airflow! foo ^^ : {foo_val}'"
    )

    t2 = BashOperator(
        task_id="print_date",
        bash_command="date"
    )
    
    t3 = PythonOperator(
        task_id="simple_hello",
        python_callable=simple_hello
    )
    
    #t4 = say_hello(name="Nice-Airflow")

    
    t1 >> t2 >> t3 >> say_hello(name="Nice-Airflow")

