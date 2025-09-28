from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

import os
import sys
import logging
from logging import Logger, getLogger

#sys.path.append(os.path.join(os.path.dirname(__file__), "../debug_dag_k8s"))

from debug_dag_k8s._dump_pod_evidence import dump_pod_evidence

logger: Logger = getLogger(__name__)

    
def _evidence_template(**context):
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
    dag_id="_evidence_template",
    schedule=None,
    tags=['evidence_template'],
    default_args={
        'owner': 'a001',
        'start_date': datetime(2025, 5, 21),
        'retries': 10,
        'retry_delay': timedelta(minutes=1),
        'retry_exponential_backoff': True,         # 재시도 간격 점증
        'max_retry_delay': timedelta(minutes=30),  # (선택) 상한
        'on_failure_callback': dump_pod_evidence,  # ★ 실패 시 K8s 증거 수집
        'execution_timeout': timedelta(hours=2),   # ★ 태스크 단위 타임아웃
    },
    max_active_tasks=3,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=6),             # ★ DAG Run 전체 타임아웃
) as dag:
    evidence_template = PythonOperator(
        task_id="evidence_template",
        python_callable=_evidence_template,
        # on_failure_callback=debug_error_callback,
        # on_success_callback=debug_success_callback,        
    )
    
    evidence_template