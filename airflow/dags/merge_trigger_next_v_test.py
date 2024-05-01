from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from pytz import timezone
import json
import sys
import os

sys.path.append('/opt/airflow/modules')

from bunjang_crawler import collect_and_filter_data, save_to_json, update_products, get_updated_products
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1, 14, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'merge_trigger_v3_test',
    default_args=default_args,
    description='Bunjang crawler DAG with merge trigger',
    schedule_interval='30 14 * * *',
    catchup=False,
)

def crawl_and_filter_brand(brand, **kwargs):
    today = datetime.now().strftime("%Y%m%d")
    output_file = f"/opt/airflow/output/{brand[0]}_{today}_products.json"
    collect_and_filter_data(brand, output_file)


def compare_brand_data(brand, **kwargs):
    today = datetime.now().strftime("%Y%m%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    today_file = f"/opt/airflow/output/{brand[0]}_{today}_products.json"
    yesterday_file = f"/opt/airflow/output/{brand[0]}_{yesterday}_products.json"

    with open(today_file, "r", encoding="utf-8") as file:
        today_data = json.load(file)

    if os.path.exists(yesterday_file):
        with open(yesterday_file, "r", encoding="utf-8") as file:
            yesterday_data = json.load(file)

        updated_data = get_updated_products(yesterday_data, today_data)
        output_file = f"/opt/airflow/output/{brand[0]}_update_{today}.json"
        save_to_json(updated_data, output_file)
    else:
        output_file = f"/opt/airflow/output/{brand[0]}_update_{today}.json"
        save_to_json(today_data, output_file)


with open("/opt/airflow/data/brands.json", "r", encoding="utf-8") as file:
    brand_names = json.load(file)

for brand in brand_names.items():
    crawl_task = PythonOperator(
        task_id=f"crawl_and_filter_{brand[0]}",
        python_callable=crawl_and_filter_brand,
        op_kwargs={"brand": brand},
        dag=dag,
        pool='merge_trigger_pool',
    )

    compare_task = PythonOperator(
        task_id=f"compare_brand_data_{brand[0]}",
        python_callable=compare_brand_data,
        op_kwargs={"brand": brand},
        dag=dag,
        pool='merge_trigger_pool',
    )

    trigger_merge_task = TriggerDagRunOperator(
        task_id=f"trigger_merge_{brand[0]}",
        trigger_dag_id="merge_v3_test",
        conf={"brand": brand[0]},
        dag=dag,
        pool='merge_trigger_pool',
    )

    crawl_task >> compare_task >> trigger_merge_task