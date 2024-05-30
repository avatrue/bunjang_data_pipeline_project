FROM apache/airflow:2.8.4

USER root
RUN apt-get update && apt-get install -y \
    libev-dev \
    gcc \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev

COPY requirements.txt /requirements.txt

# 권한을 설정하고 pip 설치
RUN chown airflow: /requirements.txt
USER airflow

RUN pip install --no-cache-dir -r /requirements.txt
