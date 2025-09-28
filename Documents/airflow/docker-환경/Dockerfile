FROM apache/airflow:2.9.2-python3.11
# docker build -t airflow:2.9.2-vim .

# vi, vim 설치
USER root
RUN apt-get update && \
    apt-get install -y vim tree procps ftp net-tools postgresql-client-16 && \
    rm -rf /var/lib/apt/lists/*


# alias 설정 (모든 사용자에 적용되도록 /etc/bash.bashrc 수정)
RUN echo 'alias ll="ls -al"' >> /etc/bash.bashrc

# airflow 유저로 다시 전환
USER airflow