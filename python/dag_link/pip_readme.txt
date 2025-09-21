
@venv /general_templates/Documents/python/venv.txt
--------------------------------------------------------------
    D:\py_venv
    Scripts\activate.bat
--------------------------------------------------------------


# Airflow 쪽은 버전마다 의존성 충돌이 잦아서, 그냥 pip install apache-airflow==2.9.2 하면 보통 깨집니다.
# 공식에서 권장하는 방식은 제약 파일(constraints file) 을 함께 쓰는 거예요.

# Python 3.9
pip install "apache-airflow==2.9.2" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.2/constraints-3.11.txt"
