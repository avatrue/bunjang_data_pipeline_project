from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from pytz import timezone
import json
import sys
import os



from modules.bunjang_crawler import collect_and_filter_data, save_to_json, update_products, get_updated_products
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
    output_file = f"../output/{brand[0]}_{today}_products.json"
    collect_and_filter_data(brand, output_file)


def compare_brand_data(brand, **kwargs):
    today = datetime.now().strftime("%Y%m%d")
    today_file = f"../output/{brand[0]}_{today}_products.json"

    with open(today_file, "r", encoding="utf-8") as file:
        today_data = json.load(file)

    max_days_ago = 3
    for days_ago in range(1, max_days_ago + 1):
        prev_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y%m%d")
        prev_file = f"../output/{brand[0]}_{prev_date}_products.json"

        if os.path.exists(prev_file):
            with open(prev_file, "r", encoding="utf-8") as file:
                prev_data = json.load(file)
            updated_data = get_updated_products(prev_data, today_data)
            output_file = f"../output/{brand[0]}_update_{today}.json"
            save_to_json(updated_data, output_file)
            break
    else:
        output_file = f"../output/{brand[0]}_update_{today}.json"
        save_to_json(today_data, output_file)

with open("../data/brands.json", "r", encoding="utf-8") as file:
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