#!/bin/sh
#
# home path : /root/airflow-docker/start.sh
# 
set -eu


# 속편하게 지우고 시작하는게 추천. (dag 만 보존, db는 날라감.)
docker rm -f airflow-standalone

NAME=${NAME:-airflow-standalone}
IMAGE=${IMAGE:-apache/airflow:2.9.2-python3.11}
PORT=${PORT:-18080}
DAGS_DIR=${DAGS_DIR:-"$PWD/dags"}
MEM=${MEM:-2g}
CPUS=${CPUS:-2}

exists()  { docker ps -a --format '{{.Names}}' | grep -Fxq "$NAME"; }
running() { [ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null || echo false)" = "true" ]; }

start_existing() {
  echo "▶ starting existing container: $NAME"
  docker start "$NAME" >/dev/null
}

create_new() {
  echo "▶ creating new container: $NAME"
  mkdir -p "$DAGS_DIR"
  docker run -d --name "$NAME" \
    -p "$PORT:8080" \
    -v "$DAGS_DIR:/opt/airflow/dags" \
    -e _AIRFLOW_WWW_USER_USERNAME=admin \
    -e _AIRFLOW_WWW_USER_PASSWORD=admin123 \
    -e AIRFLOW__CORE__LOAD_EXAMPLES=False \
    -e AIRFLOW__CORE__PARALLELISM=1 \
    -e AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG=1 \
    -e AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=30 \
    -e AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL=30 \
    -e AIRFLOW__WEBSERVER__WORKERS=1 \
    --memory="$MEM" --cpus="$CPUS" \
    "$IMAGE" bash -lc "airflow standalone" >/dev/null
}

wait_ready() {
  echo "⏳ waiting for Airflow at http://localhost:$PORT ..."
  i=0
  until curl -fsS "http://localhost:$PORT/health" >/dev/null 2>&1; do
    i=$((i+1))
    [ $i -ge 600 ] && { echo "❌ timeout. last logs:"; docker logs --tail=100 "$NAME"; exit 1; }
    sleep 2
  done
  echo "✅ Airflow is up → http://localhost:$PORT"
}

if exists; then
  if running; then
    echo "⚠️  $NAME already running. nothing to do."
    exit 0
  else
    start_existing
  fi
else
  create_new
fi

wait_ready

