from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from pytz import timezone
from cassandra.cluster import Cluster
import json
import os
import threading
import sys

sys.path.append('/opt/airflow/modules')
from bunjang_crawler import update_products, save_to_json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 27, 12, 0),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'merge_v3_test',
    default_args=default_args,
    description='Bunjang crawler merge DAG',
    schedule_interval=None,
    max_active_runs=1,
)


def merge_results_task(**kwargs):
    brand = kwargs['dag_run'].conf.get('brand', 'default_brand')
    today = datetime.now().strftime("%Y%m%d")
    input_file = f"/opt/airflow/output/{brand}_update_{today}.json"

    print(f"Starting merge task for brand: {brand}")
    print(f"Input file: {input_file}")

    with open(input_file, "r", encoding="utf-8") as file:
        update_data = json.load(file)
        print(f"Loaded {len(update_data)} records from {input_file}")

    cluster = Cluster(['cassandra'])
    session = cluster.connect('bunjang')

    for product in update_data:
        # 카산드라에있는지 확인
        result = session.execute(
            """
            SELECT * FROM products WHERE pid = %s
            """,
            (product['pid'],)
        )

        if result:
            existing_product = result.one()

            # 브랜드 업데이트
            brands = set(existing_product.brands)
            brands.update(product['brands'])

            # 시간:가격 값 업데이트
            price_updates = existing_product.price_updates
            new_price_updates = product['price_updates']

            for update in new_price_updates:
                update_time = list(update.keys())[0]
                if update_time not in [list(p.keys())[0] for p in price_updates]:
                    price_updates.append(update)

            # 상태 업데이트
            status = product['status'] if product['status'] != existing_product.status else existing_product.status

            session.execute(
                """
                UPDATE products
                SET brands = %s, name = %s, price_updates = %s, product_image = %s, status = %s, category_id = %s
                WHERE pid = %s
                """,
                (
                    list(brands),
                    product['name'],
                    price_updates,
                    product['product_image'],
                    status,
                    product['category_id'],
                    product['pid']
                )
            )
            print(f"업데이트: pid: {product['pid']}")
        else:
            # 제품 추가
            session.execute(
                """
                INSERT INTO products (pid, brands, name, price_updates, product_image, status, category_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    product['pid'],
                    product['brands'],
                    product['name'],
                    product['price_updates'],
                    product['product_image'],
                    product['status'],
                    product['category_id']
                )
            )
            print(f"제품추가: pid: {product['pid']}")

    print(f"Merge task 완료: {brand}")

merge_task = PythonOperator(
    task_id='merge_results',
    python_callable=merge_results_task,
    provide_context=True,
    dag=dag,
    pool='merge_pool',
)