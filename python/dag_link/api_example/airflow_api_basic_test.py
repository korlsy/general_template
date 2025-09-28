from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
from requests.auth import HTTPBasicAuth

AIRFLOW_USER = "admin"
AIRFLOW_PASS = "admin"
#BASE_URL = "http://host.docker.internal:18080"
BASE_URL = "http://172.25.84.229:18080"

def list_dags_basic():
    url = f"{BASE_URL}/api/v1/dags?limit=10"
    r = requests.get(url, auth=HTTPBasicAuth(AIRFLOW_USER, AIRFLOW_PASS), timeout=10)
    r.raise_for_status()
    return r.json()  # XCom에 자동 저장됨

with DAG(
    dag_id="airflow_api_basic_test",
    start_date=datetime(2024, 1, 1),
    schedule="@once",
    catchup=False,
    tags=["test", "airflow-api", "basic-auth"],
) as dag:
    list_dags = PythonOperator(
        task_id="list_dags_via_basic_auth",
        python_callable=list_dags_basic,
    )
