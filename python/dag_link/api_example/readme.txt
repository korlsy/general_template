
2.9.2 : token 방식 not support.

# docker 시작시 아래 옵션 추가.
# -e AIRFLOW__API__AUTH_BACKENDS=airflow.providers.fab.auth_manager.api.auth.backend.basic_auth \

# curl "http://localhost:18080/api/v1/health"
# curl -u "admin:admin" "http://localhost:18080/api/v1/dags?limit=10" -H "Accept: application/json"
# curl -u "admin:admin" -H "Accept: application/json" "http://localhost:18080/api/v1/dags?limit=20"


docker 에서 host.
host : host.docker.internal 또는 ip (hostname -I)