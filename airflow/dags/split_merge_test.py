from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from pytz import timezone
import json
import requests
import sys
from queue import Queue

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
    'split_merge_test',
    default_args=default_args,
    description='Bunjang crawler DAG',
    schedule_interval='0 12 * * *',
    catchup=False,
)

merge_queue = Queue()

def crawl_and_filter_brand(brand, **kwargs):
    output_file = f"/opt/airflow/output/{brand[0]}_products.json"
    collect_and_filter_data(brand, output_file)
    merge_queue.put(brand)

def merge_results_task(**kwargs):
    while not merge_queue.empty():
        brand = merge_queue.get()
        input_dir = "/opt/airflow/output"
        output_file = "/opt/airflow/output/all_products.json"
        merge_results(input_dir, output_file)

with open("/opt/airflow/data/brands.json", "r", encoding="utf-8") as file:
    brand_names = json.load(file)

for brand in brand_names.items():
    crawl_task = PythonOperator(
        task_id=f"crawl_and_filter_{brand[0]}",
        python_callable=crawl_and_filter_brand,
        op_kwargs={"brand": brand},
        dag=dag,
    )

merge_task = PythonOperator(
    task_id="merge_results",
    python_callable=merge_results_task,
    dag=dag,
)

for brand in brand_names.items():
    crawl_task = f"crawl_and_filter_{brand[0]}"
    dag.get_task(crawl_task) >> merge_task