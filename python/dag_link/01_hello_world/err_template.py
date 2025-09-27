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

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(seconds=5),
}

import logging
import traceback

def _error_template(**context):
    logger = logging.getLogger("airflow.task")

    try:
        logger.info("작업 시작")
        
        result = 1 / 0
        logger.info("쿼리 결과: %s", result)

    except Exception as e:
        logger.error("에러 발생: %s", str(e))
        logger.error("Traceback:\n%s", traceback.format_exc())
        raise
    else:
        logger.info("작업 정상 완료")
    finally:
        logger.info("리소스 정리 또는 후처리")
        

with DAG(
    dag_id="err_template",
    default_args=default_args,
    description="",
    schedule=None,
    start_date=pendulum.datetime(2025, 9, 1, 0, 0, tz=pendulum.timezone("Asia/Seoul")),
    catchup=False,
    tags=["template"],
) as dag:
    error_template = PythonOperator(
        task_id="error_template_task",
        python_callable=_error_template
    )
    
    error_template

