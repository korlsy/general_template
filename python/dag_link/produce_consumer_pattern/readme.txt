
# 워커 시작(스케줄러가 매 1분마다 소비)
airflow dags trigger worker_consumer
# 컨트롤러로 여러 번 적재해 보세요
airflow dags trigger controller_enqueue --conf '{"num_jobs": 100, "tag":"batch-A"}'
airflow dags trigger controller_enqueue --conf '{"num_jobs": 37,  "tag":"batch-B"}'

gpt link : https://chatgpt.com/g/g-p-6897606b433c81918aa1f6e09efdbcb1/c/68d53a77-4ddc-8322-b0d7-04b00167e668

왜 이 구성이 편한가
    경합 안전: FOR UPDATE SKIP LOCKED로 다중 워커여도 중복 소비 없음
    K개 청크: 워커 1회당 K개만 집어서 처리 → 과부하·타임아웃 방지
    상태 가시성: DB가 진짜 소스 오브 트루스 → queued/processing/done/error를 SQL로 바로 집계
    Airflow는 스케줄만: 실패/재시도/병렬성은 Airflow가, 세밀한 단위 상태는 DB가 담당