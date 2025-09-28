from __future__ import annotations
import random, string, json
from datetime import datetime
from airflow import DAG
from airflow.decorators import task
from airflow.models.param import Param
from airflow.providers.postgres.hooks.postgres import PostgresHook

# 이 Conn ID만 맞추면 바로 동작
QUEUE_CONN_ID = "_pg_queue_db"

with DAG(
    dag_id="_pc_controller_enqueue",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # 수동 트리거
    catchup=False,
    params={
        "num_jobs": Param(25, type="integer", minimum=1, maximum=10000, description="적재할 작업 수"),
        "tag": Param("demo", type="string", description="페이로드 태그"),
    },
    doc_md="""
**역할:** 큐 테이블(job_queue)에 작업(payload)을 쌓기만 합니다.
""",
) as dag:

    @task
    def enqueue(num_jobs: int, tag: str):
        pg = PostgresHook(postgres_conn_id=QUEUE_CONN_ID)
        rows = []
        for _ in range(num_jobs):
            rid = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
            payload = {
                "rid": rid,
                "op": "toy_work",   # 워커가 무엇을 할지 구분용
                "tag": tag,
                "value": random.randint(1, 100),
            }
            rows.append(json.dumps(payload))

        # 벌크 insert
        insert_sql = """
        INSERT INTO job_queue (payload) 
        SELECT x::jsonb
        FROM unnest(%s::text[]) AS t(x);
        """
        pg.run(insert_sql, parameters=(rows,))
        return {"inserted": len(rows)}

    enqueue(dag.params["num_jobs"], dag.params["tag"])
