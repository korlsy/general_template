#!/bin/bash
CMD="kubectl get app -n argocd -o wide"

print_title () {
  local text=" $1 "
  local width=100
  local pad=$(( (width - ${#text}) / 2 ))
  printf '=%.0s' $(seq 1 $pad)
  printf "%s" "$text"
  printf '=%.0s' $(seq 1 $((width - pad - ${#text})))
  echo
}

print_title "명령"
echo "$CMD"

print_title "결과"
eval "$CMD"