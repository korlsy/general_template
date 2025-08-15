kubectl apply -f app-$APP.restore.yaml
# 자동 동기화였다면 바로 붙습니다.
# 수동 동기화라면:
argocd app sync $APP


