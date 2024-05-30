from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from pytz import timezone
import logging
import os
from pyspark.sql import SparkSession
import happybase

def spark_hbase_fetcher(**kwargs):
    HBASE_HOST = os.getenv("HBASE_HOST")

    # Spark 세션 생성
    spark = SparkSession.builder \
        .appName("HBaseFetcher") \
        .getOrCreate()

    # HBase 연결
    connection = happybase.Connection(HBASE_HOST)
    table = connection.table('financial_data')

    # HBase에서 데이터 가져오기
    rows = table.scan()
    data = []
    for key, value in rows:
        data.append(value)

    # 가져온 데이터를 Spark DataFrame으로 변환
    df = spark.createDataFrame(data)
    
    # 데이터 확인
    df.show()

    # DataFrame을 로깅
    logging.info(f"Fetched data from HBase: {df.collect()}")

    # Spark 세션 종료
    spark.stop()


logging.basicConfig(level=logging.INFO)

KST = timezone("Asia/Seoul")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 4, 1, 19, 0, 0, tzinfo=KST),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "spark_hbase_fetcher",
    default_args=default_args,
    description="Fetch data from HBase using Spark",
    schedule_interval=None,  # 수동으로 실행
    catchup=False,
)

fetch_hbase_data_task = PythonOperator(
    task_id="fetch_hbase_data",
    python_callable=spark_hbase_fetcher,
    dag=dag,
    provide_context=True,
)

fetch_hbase_data_task
