from __future__ import annotations
import time
from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook

QUEUE_CONN_ID = "queue_db"
BATCH_SIZE = 10        # 한 번에 소비할 개수(K)
LOCK_TIMEOUT_SEC = 5   # 행 잠금 대기 시간(짧게)

with DAG(
    dag_id="_pc_worker_consumer",
    start_date=datetime(2024, 1, 1),
    schedule="*/1 * * * *",  # 매 1분 소비
    catchup=False,
    max_active_runs=1,        # 중복 소비 방지(필요 시 조정)
    doc_md="""
**역할:** 큐(job_queue)에서 `queued` 상태를 **K개만** 안전하게 잠그고(SELECT ... FOR UPDATE SKIP LOCKED)
처리 후 `done/error`로 마감합니다. Airflow는 스케줄만, 상태관리는 DB가 담당.
""",
) as dag:

    @task
    def consume_batch():
        pg = PostgresHook(postgres_conn_id=QUEUE_CONN_ID)

        # 짧은 lock timeout (다른 워커와 경합 시 빠르게 포기)
        pg.run("SET LOCAL lock_timeout = %s;", parameters=(f"{LOCK_TIMEOUT_SEC}s",), autocommit=False)

        # 1) K개 잠그고 processing으로 마킹
        claim_sql = f"""
        WITH cte AS (
          SELECT id
          FROM job_queue
          WHERE status = 'queued'
          ORDER BY id
          FOR UPDATE SKIP LOCKED
          LIMIT {BATCH_SIZE}
        )
        UPDATE job_queue q
        SET status = 'processing', started_at = now(), attempts = attempts + 1
        FROM cte
        WHERE q.id = cte.id
        RETURNING q.id, q.payload::text;
        """

        # 트랜잭션 단위 처리
        conn = pg.get_conn()
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                cur.execute(claim_sql)
                claimed = cur.fetchall()  # [(id, payload_json_text), ...]
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        if not claimed:
            return {"claimed": 0, "done": 0}

        # 2) 실처리 (여기서 실제 업무 로직 수행)
        done_ids, error_results = [], []
        for _id, payload_text in claimed:
            try:
                # --- 예시 업무: 0.1초 슬립 + value 제곱 계산 ---
                # 실제론 외부 API/DB/S3/Spark/KPO 호출 등으로 대체
                time.sleep(0.1)
                # 가벼운 검증
                # (json.loads 쓰지 않고 DB내 jsonb도 좋지만, 단순화를 위해 생략)
                # payload_text는 텍스트이므로 여기선 로깅만
                # print(f"[DO] id={_id} payload={payload_text[:120]}")
                done_ids.append(_id)
            except Exception as e:
                error_results.append((_id, str(e)))

        # 3) 상태 갱신: done / error
        try:
            with conn.cursor() as cur:
                if done_ids:
                    cur.execute(
                        "UPDATE job_queue SET status='done', finished_at=now(), err=NULL WHERE id = ANY(%s);",
                        (done_ids,),
                    )
                for eid, emsg in error_results:
                    cur.execute(
                        "UPDATE job_queue SET status='error', finished_at=now(), err=%s WHERE id=%s;",
                        (emsg, eid),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return {
            "claimed": len(claimed),
            "done": len(done_ids),
            "error": len(error_results),
        }

    consume_batch()
