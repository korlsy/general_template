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
from common import with_task_logging

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(seconds=5),
}

import logging
import traceback

logger = logging.getLogger(__name__)

@with_task_logging(logger=logger)
def _error_template_deco(**context):
    logger.info("비지니스 로직!!")
    res = 1/0
    logger.info("res = %s", res)
        
with DAG(
    dag_id="err_template_decorator",
    default_args=default_args,
    description="",
    schedule=None,
    start_date=pendulum.datetime(2025, 9, 1, 0, 0, tz=pendulum.timezone("Asia/Seoul")),
    catchup=False,
    tags=["template"],
) as dag:
    logging.info("start!!!")
    
    error_template = PythonOperator(
        task_id="error_template_task",
        python_callable=_error_template_deco
    )
    
    error_template

