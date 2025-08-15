#!/usr/bin/env bash
set -euo pipefail
APP=${1:?Usage: $0 <app-name>}
NS=${2:-argocd}
MODE=${3:-keep}  # keep(리소스 보존) | purge(리소스까지 삭제)

# 1) 백업
kubectl get application "$APP" -n "$NS" -o yaml > "app-$APP.full.yaml"
yq '
  del(.status) |
  del(.metadata.uid, .metadata.resourceVersion, .metadata.generation, .metadata.creationTimestamp, .metadata.managedFields, .metadata.annotations."kubectl.kubernetes.io/last-applied-configuration") |
  .metadata |= (.name="'"$APP"'" | .namespace="'"$NS"'")
' "app-$APP.full.yaml" > "app-$APP.restore.yaml"

echo "[INFO] Backup done: app-$APP.full.yaml / app-$APP.restore.yaml"

# 2) 삭제
if [[ "$MODE" == "keep" ]]; then
  echo "[INFO] Deleting Application ONLY (keeping workloads)"
  if argocd app get "$APP" >/dev/null 2>&1; then
    argocd app delete "$APP" --cascade=false --yes || true
  else
    kubectl patch application "$APP" -n "$NS" -p '{"metadata":{"finalizers":[]}}' --type=merge || true
    kubectl delete application "$APP" -n "$NS" || true
  fi
else
  echo "[WARN] Deleting Application AND its resources"
  argocd app delete "$APP" --cascade=true --yes || kubectl delete application "$APP" -n "$NS"
fi

echo "[INFO] Application deleted. To restore: kubectl apply -f app-$APP.restore.yaml && argocd app sync $APP"
