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
import logging
import traceback
from airflow.models.taskinstance import TaskInstance


sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from common import check_port
from retry_callback import rich_on_retry_callback
from debug_utils import on_fail, on_success


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")


logger = logging.getLogger(__name__) # "airflow.task"


# def retry_callback(context):
#     ti = context['ti']   # TaskInstance 객체
#     dag_id = context['dag'].dag_id
#     task_id = context['task'].task_id
#     try_number = context['ti'].try_number
#     logger.info(f"[{dag_id}.{task_id}] {try_number}번째 재시도!")




default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(seconds=10),
    "start_date":pendulum.datetime(2025, 9, 1, 0, 0, tz=pendulum.timezone("Asia/Seoul")),
    "on_retry_callback": rich_on_retry_callback,
    
}

def debug_error_callback(context):
    ti: TaskInstance = context.get("task_instance")
    
    dag_id = context.get("dag").dag_id if context.get("dag") else None
    logger.error(f"[DEBUG-FAILURE] Task failed: dag={dag_id}, task={ti.task_id}, try={ti.try_number}")
    logger.error(f"[DEBUG-FAILURE] Exception: {context.get('exception')}")
    logger.error(f"[DEBUG-FAILURE] Log url: {context.get('task_instance').log_url}")

def debug_success_callback(context):
    ti = context["task_instance"]
    logger.info(f"[DEBUG-SUCCESS] Task succeeded: {ti.task_id}, try={ti.try_number}")



    
def _error_template(**context):
    try:
        logger.info("작업 시작")
        
        result = 0
        #result = 1 / 0
        logger.info("쿼리 결과: %s", result)
        logger.info("="*100)
        logger.info("end!!!")
    except Exception as e:
        logger.error("에러 발생: %s", str(e))
        #logger.error("Traceback:\n%s", traceback.format_exc())
        raise
    else:
        logger.info("작업 정상 완료")
    finally:
        logger.info("리소스 정리 또는 후처리")
        

with DAG(
    dag_id="_err_template",
    default_args=default_args,
    schedule=None,
    catchup=False,
    tags=["template"],
    description="",
    
    # - 로컬 선언.
    # on_failure_callback=debug_error_callback,
    # on_success_callback=debug_success_callback,
    
    # - debug_utils.py 선언.
    # on_failure_callback=on_fail,
    # on_success_callback=on_success,
    # dagrun_timeout=timedelta(hours=4),# queue 장기정체/좀비 잡기    
) as dag:
    error_template = PythonOperator(
        task_id="error_template_task",
        python_callable=_error_template,
        on_failure_callback=debug_error_callback,
        on_success_callback=debug_success_callback,        
    )
    
    error_template

