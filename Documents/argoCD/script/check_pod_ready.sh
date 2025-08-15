#!/usr/bin/env bash
# check_argocd_pods_ready.sh
# argocd 네임스페이스의 모든 파드가 READY(예: 1/1, 2/2)일 때만 성공.
# 모두 READY가 되면 선택적으로 후속 명령(-c)을 실행.

set -u
set -o pipefail

NS="${1:-argocd}" # 첫 번째 인자로 네임스페이스 받음. 기본값 argocd
TIMEOUT=600     # 전체 대기 한도(초)
INTERVAL=5      # 루프 간격(초)
POST_CMD=""

usage() {
  cat <<EOF
Usage: $0 [-n NAMESPACE] [-t TIMEOUT_SEC] [-i INTERVAL_SEC] [-c "COMMAND"]
  -n  네임스페이스 (기본: argocd)
  -t  전체 타임아웃 초 (기본: 600)
  -i  루프 간격 초 (기본: 5)
  -c  성공 시 실행할 명령 (예: -c "./next.sh")
EOF
}

while getopts ":n:t:i:c:h" opt; do
  case "$opt" in
    n) NS="$OPTARG" ;;
    t) TIMEOUT="$OPTARG" ;;
    i) INTERVAL="$OPTARG" ;;
    c) POST_CMD="$OPTARG" ;;
    h) usage; exit 0 ;;
    \?) echo "알 수 없는 옵션: -$OPTARG" >&2; usage; exit 2 ;;
    :)  echo "옵션 -$OPTARG 에 값이 필요합니다." >&2; usage; exit 2 ;;
  esac
done

ts() { date "+%F %T"; }
log() { echo "[$(ts)] $*"; }
die() {
  echo "[$(ts)] 실패: $*" >&2
  echo "------ 현재 파드 (요약) ------"
  kubectl -n "$NS" get pods -o wide || true
  echo "------------------------------"
  exit 1
}
rem_secs(){ echo $(( DEADLINE - $(date +%s) )); }

command -v kubectl >/dev/null 2>&1 || { echo "kubectl 이 필요합니다."; exit 2; }

DEADLINE=$(( $(date +%s) + TIMEOUT ))

log "Kubernetes API health 체크..."
until kubectl get --raw='/healthz' 2>/dev/null | grep -q '^ok'; do
  [[ $(rem_secs) -le 0 ]] && die "Kubernetes API 가 응답하지 않습니다."
  sleep "$INTERVAL"
done
log "API ok"

log "네임스페이스 존재 확인: $NS"
until kubectl get ns "$NS" >/dev/null 2>&1; do
  [[ $(rem_secs) -le 0 ]] && die "네임스페이스 $NS 를 찾을 수 없습니다."
  sleep "$INTERVAL"
done

log "argocd 파드 READY(컨테이너 준비율) 상태 대기 시작..."

while : ; do
  left=$(rem_secs); (( left <= 0 )) && die "타임아웃(${TIMEOUT}s) 초과"

  # NAME READY STATUS RESTARTS AGE
  lines="$(kubectl -n "$NS" get pods --no-headers 2>/dev/null || true)"

  if [[ -z "${lines// }" ]]; then
    log "체크 중: 아직 파드가 없습니다. (남은 ${left}s)"
    sleep "$INTERVAL"
    continue
  fi

  total=0
  ready_ok=0
  not_ready_lines=()

  # shellcheck disable=SC2162
  while read name readycol status rest; do
    [[ -z "${name:-}" ]] && continue
    (( total++ ))
    want="${readycol#*/}"   # 분모
    have="${readycol%/*}"   # 분자
    if [[ "$want" == "$have" && "$want" != "0" ]]; then
      (( ready_ok++ ))
    else
      not_ready_lines+=("$name $readycol $status")
    fi
  done <<< "$lines"

  if (( ready_ok == total )); then
    log "✅ 모든 파드 READY (${ready_ok}/${total})"
    break
  else
    log "체크 중: READY ${ready_ok}/${total} (남은 ${left}s)"
    if (( ${#not_ready_lines[@]} > 0 )); then
      echo "  -> 미완료 목록:"
      for l in "${not_ready_lines[@]}"; do
        # 예: argocd-server 0/1 Pending -> ' - argocd-server [0/1 Pending]'
        printf "     - %s [%s %s]\n" "$(cut -d' ' -f1 <<<"$l")" "$(cut -d' ' -f2 <<<"$l")" "$(cut -d' ' -f3- <<<"$l")"
      done
    fi
    sleep "$INTERVAL"
  fi
done

# 성공 시 후속 명령 실행
if [[ -n "${POST_CMD}" ]]; then
  log "후속 명령 실행: ${POST_CMD}"
  bash -lc "${POST_CMD}"
  rc=$?
  log "후속 명령 종료 코드: ${rc}"
  exit "${rc}"
fi

exit 0
