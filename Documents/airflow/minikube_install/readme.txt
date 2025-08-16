gpt airflow 설치 관련.

# (권장) 차트 인덱스 최신화
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# 네임스페이스 생성 후 설치
kubectl create ns airflow
helm install airflow apache-airflow/airflow -n airflow -f values-minikube.yaml


# Minikube IP 확인
minikube ip  # 예: 192.168.49.2

# 브라우저에서 접속
http://<minikube-ip>:30080



kubectl -n airflow port-forward svc/airflow-webserver 8080:8080
# http://localhost:8080
``` :contentReference[oaicite:5]{index=5}

---
혹은 NodePort 대신 포트포워딩을 원하면:
	### DAG 테스트는 이렇게 가볍게
	- 위에서 `AIRFLOW__CORE__LOAD_EXAMPLES=True`를 넣었으니, UI에 예제 DAG들이 바로 보일 거예요. 그중 하나 돌려보면 설치 검증 끝. (`example_*` DAG들)  
	- 직접 간단한 DAG도 올리고 싶다면, 차트 기본 설정에서는 `/opt/airflow/dags`가 마운트되어 있으니 다음 중 하나로:
	  - `kubectl -n airflow exec -it deploy/airflow-scheduler -- bash` 후 `/opt/airflow/dags/hello.py` 생성
	  - 또는 `port-forward` 켠 상태에서 UI에서 “Browse → DAGs”에서 리프레시
	
	---
	
	필요하면 지금 쓰신 `values-minikube.yaml` 일부 보여줘요. 어디를 지우고 어디를 옮기면 되는지 딱 맞게 패치 형태로 정리해줄게요.
	::contentReference[oaicite:6]{index=6}
