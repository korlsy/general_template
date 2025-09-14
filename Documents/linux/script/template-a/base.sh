#!/usr/bin/env bash
#set -euo pipefail

IFS=$'\n\t'

if [[ -z "${BASH_VERSINFO:-}" || "${BASH_VERSINFO[0]}" -lt 4 ]]; then
  echo "This framework requires Bash >= 4" >&2; exit 2
fi

declare -A OPTS=()
OPTS_FLAGS=()
LOG_FILE=""
ASSUME_YES="false"
SCRIPT_NAME="${SCRIPT_NAME:-$(basename "${BASH_SOURCE[-1]}")}"

log() {
  local ts; ts="$(date '+%Y-%m-%d %H:%M:%S')"
  printf '%s %s\n' "$ts" "$*"
  if [[ -n "$LOG_FILE" ]]; then
    printf '%s %s\n' "$ts" "$*" >> "$LOG_FILE" || true
  fi
  return 0
}

get_opt() { local k="$1" d="${2:-}"; echo "${OPTS[$k]:-$d}"; }
has_flag(){ local f="$1"; for x in "${OPTS_FLAGS[@]:-}"; do [[ "$x" == "$f" ]] && return 0; done; return 1; }

__default_confirm() {
  local prompt="${1:-계속 진행할까요?}"
  if [[ "$ASSUME_YES" == "true" ]]; then
    #log "Auto-confirm (--yes)"
    return 0
  fi
  local ans
  read -r -p "$prompt [y/N] " ans || true
  case "${ans:-}" in
    y|Y|yes|YES) return 0 ;;
    *)
      log "사용자 취소"
      #return 1 
      exit 0 
      ;;
  esac
}

confirm() {
  if declare -F confirm_impl >/dev/null 2>&1; then confirm_impl "$@"; return; fi
  __default_confirm "$@"
}

# base.sh
hydrate_opts_to_vars() {
  local k name
  for k in "${!OPTS[@]}"; do
    # 키를 변수명으로 변환: 하이픈 → 언더스코어
    name="${k//-/_}"
    # 유효한 변수명만 허용
    if [[ "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
      # Bash 4+: 전역으로 주입
      declare -g "$name=${OPTS[$k]}"
    else
      log "옵션 키 '$k' 는 변수명으로 부적합하여 스킵"
    fi
  done
}



parse_kv_args() {
  local key val
  while (( $# )); do
    case "$1" in
      -h|--help)
        if declare -F usage >/dev/null 2>&1; then usage; fi
        exit 0
        ;;

      # --key=value
      --*=*)
        key="${1%%=*}"; key="${key#--}"
        val="${1#*=}"
        OPTS["$key"]="$val"
        shift
        ;;

      # -key=value   ← 단일 하이픈 + = 도 지원
      -*=*)
        key="${1%%=*}"; key="${key#-}"
        val="${1#*=}"
        OPTS["$key"]="$val"
        shift
        ;;

      # --key value  (value가 다음 인자)
      --*)
        key="${1#--}"
        if [[ $# -ge 2 && ! "$2" =~ ^- ]]; then
          OPTS["$key"]="$2"
          shift 2
        else
          OPTS_FLAGS+=("$key")
          shift
        fi
        ;;

      # -key value   (value가 다음 인자)
      -*)
        key="${1#-}"
        if [[ $# -ge 2 && ! "$2" =~ ^- ]]; then
          OPTS["$key"]="$2"
          shift 2
        else
          OPTS_FLAGS+=("$key")
          shift
        fi
        ;;

      # 그 외 토큰은 무시
      *)
        shift
        ;;
    esac
  done

  # --log-file 기본값 세팅(없으면 실행 스크립트명 기반 .log)
  if [[ -n "${OPTS[log-file]:-}" ]]; then
    LOG_FILE="${OPTS[log-file]}"
  else
    local caller="${BASH_SOURCE[1]:-$0}"
    local dir="$(cd "$(dirname "$caller")" && pwd)"
    local base="$(basename "$caller")"
    LOG_FILE="${dir}/${base%.*}.log"
  fi

  # --yes 플래그 반영
  ASSUME_YES=$([[ " ${OPTS_FLAGS[*]-} " == *" yes "* ]] && echo "true" || echo "false")
}



parse_kv_args_old() {
  local key val
  while (( $# )); do
    case "$1" in
      -h|--help) if declare -F usage >/dev/null 2>&1; then usage; fi; exit 0 ;;
      --*=*) key="${1%%=*}"; key="${key#--}"; val="${1#*=}"; OPTS["$key"]="$val"; shift ;;
      --*)   key="${1#--}"; if [[ $# -ge 2 && ! "$2" =~ ^- ]]; then OPTS["$key"]="$2"; shift 2; else OPTS_FLAGS+=("$key"); shift; fi ;;
      -*)    key="${1#-}";  if [[ $# -ge 2 && ! "$2" =~ ^- ]]; then OPTS["$key"]="$2"; shift 2; else OPTS_FLAGS+=("$key"); shift; fi ;;
      *) shift ;;
    esac
  done

  #[[ -n "${OPTS[log-file]:-}" ]] && LOG_FILE="${OPTS[log-file]}"
  if [[ -n "${OPTS[log-file]:-}" ]]; then
    LOG_FILE="${OPTS[log-file]}"
  else
	# LOG_FILE="$(cd "$(dirname "${BASH_SOURCE[-1]}")" && pwd)/app.log"
    # .sh .log 로 치환
    local script_path="${BASH_SOURCE[-1]}"
    local script_dir
    script_dir="$(cd "$(dirname "$script_path")" && pwd)"
    local script_base
    script_base="$(basename "$script_path" .sh)"
    LOG_FILE="${script_dir}/${script_base}.log"
  fi


  ASSUME_YES=$([[ " ${OPTS_FLAGS[*]-} " == *" yes "* ]] && echo "true" || echo "false")
}

run() {
  parse_kv_args "$@"

  # action 필수
  local action="${OPTS[action]:-}"
  if [[ -z "$action" ]]; then
    echo "error: require action"
    declare -F usage >/dev/null && usage
    exit 2
  fi

  # 숨은 문자 제거
  action="$(printf '%s' "$action" | tr -d '\r' | tr -d ' ')"

  # action debug
  local fn="action_${action}"
  if ! declare -F "$fn" >/dev/null 2>&1; then
    echo "not found action: $action"
    echo "action list:"
    #declare -F | awk '/action_/ {print " -",$3}'
	declare -F | awk '/action_/ {sub(/^action_/, "", $3); print " -", $3}'
    declare -F usage >/dev/null && usage
    exit 2
  fi

  #log "시작: ${SCRIPT_NAME} action=${action}"

  # 핸들러 실행 (set -e 보호)
  set +e
  "$fn"
  local rc=$?
  set -e

  if (( rc != 0 )); then
    echo "에러: action '${action}' 실행 실패 (exit=${rc})"
    exit "$rc"
  fi

  #log "완료: ${SCRIPT_NAME}"
}

