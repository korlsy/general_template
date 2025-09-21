from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import logging
import importlib
import subprocess
import sys
from lib.common import ensure_package



def task_using_requests(**context):
    ensure_package("requests", version="2.31.0")
    import requests
    res = requests.get("https://httpbin.org/get")
    logging.info("status=%s", res.status_code)


with DAG(
    dag_id="package_dyna_install",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    run_with_requests = PythonOperator(
        task_id="run_with_requests",
        python_callable=task_using_requests
    )
