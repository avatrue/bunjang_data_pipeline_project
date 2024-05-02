from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from pytz import timezone
import json
import os
import threading
import sys

sys.path.append('/opt/airflow/modules')
from bunjang_crawler import update_products, save_to_json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 27, 12, 0, tzinfo=timezone('Asia/Seoul')),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'merge_release',
    default_args=default_args,
    description='Bunjang crawler merge DAG',
    schedule_interval=None,
    max_active_runs=1,
)

def merge_results_task(**kwargs):
    brand = kwargs['dag_run'].conf.get('brand', 'default_brand')
    today = datetime.now().strftime("%Y%m%d")
    input_file = f"/opt/airflow/output/{brand}_update_{today}.json"
    output_file = "/opt/airflow/output/all_products.json"

    print(f"Starting merge task for brand: {brand}")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

    with open(input_file, "r", encoding="utf-8") as file:
        update_data = json.load(file)
        print(f"Loaded {len(update_data)} records from {input_file}")

    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as file:
            all_products = json.load(file)
            print(f"Loaded {len(all_products)} records from {output_file}")
    else:
        all_products = []
        print(f"Created new {output_file} file")

    updated_products = update_products(all_products, update_data)
    print(f"Updated {len(updated_products)} records")

    save_to_json(updated_products, output_file)
    print(f"Saved {len(updated_products)} records to {output_file}")
    print(f"Merge task completed for brand: {brand}")

merge_task = PythonOperator(
    task_id='merge_results',
    python_callable=merge_results_task,
    provide_context=True,
    dag=dag,
    pool='merge_pool',
)