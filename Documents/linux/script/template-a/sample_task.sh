#!/usr/bin/env bash
#set -euo pipefail

dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${dir}/base.sh"

usage() {
  cat <<'EOF'
Usage:
  ./sample_task.sh -action <exec|clean> [-target <path>]
Options:
  --log-file <path>  --yes -h/--help
EOF
}

action_exec() {
  confirm "confirm?" || return 1

  echo "exec-run2"
  log "test200" 
  return 0
}
action_clean()  { :; }

run "$@"

