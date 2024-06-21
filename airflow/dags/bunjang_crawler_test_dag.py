from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from pytz import timezone
import json
import requests
import sys
import os
import threading

sys.path.append('/opt/airflow/modules')
from bunjang_crawler import collect_and_filter_data, merge_results

KST = timezone('Asia/Seoul')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 27, 12, 0, tzinfo=KST),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'trigger_test_04_01_10_52',
    default_args=default_args,
    description='Bunjang crawler DAG with merge trigger',
    schedule_interval='0 12 * * *',
    catchup=False,
)

def crawl_and_filter_brand(brand, **kwargs):
    output_file = f"/opt/airflow/output/{brand[0]}_products.json"
    collect_and_filter_data(brand, output_file)

with open("/opt/airflow/data/brands_test.json", "r", encoding="utf-8") as file:
    brand_names = json.load(file)

for brand in brand_names.items():
    crawl_task = PythonOperator(
        task_id=f"crawl_and_filter_{brand[0]}",
        python_callable=crawl_and_filter_brand,
        op_kwargs={"brand": brand},
        dag=dag,
    )

    trigger_merge_task = TriggerDagRunOperator(
        task_id=f"trigger_merge_{brand[0]}",
        trigger_dag_id="merge_test_04_01_10_52",
        conf={"brand": brand[0]},
        dag=dag,
    )

    crawl_task >> trigger_merge_task

merge_lock = threading.Lock()

merge_dag = DAG(
    'merge_test_04_01_10_52',
    default_args=default_args,
    description='Bunjang crawler merge DAG',
    schedule_interval=None,
)

def merge_results_task(**kwargs):
    brand = kwargs['dag_run'].conf['brand']
    input_dir = "/opt/airflow/output"
    output_file = "/opt/airflow/output/all_products.json"
    merge_results(input_dir, output_file, merge_lock)

merge_task = PythonOperator(
    task_id='merge_results',
    python_callable=merge_results_task,
    provide_context=True,
    dag=merge_dag,
)
