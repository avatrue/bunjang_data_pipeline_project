from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from cassandra.cluster import Cluster
from elasticsearch import Elasticsearch

default_args = {
   'owner': 'airflow',
   'depends_on_past': False,
   'start_date': datetime(2023, 6, 1),
   'email_on_failure': False,
   'email_on_retry': False,
   'retries': 1,
   'retry_delay': timedelta(minutes=5),
   'pool': 'cassandra_to_elk_pool',
}

dag = DAG(
   'cassandra_to_elk',
   default_args=default_args,
   description='Cassandra to Elasticsearch',
    schedule_interval=None,
    catchup=False
)



def transfer_data():
    # Cassandra 연결 설정
    cluster = Cluster(['cassandra'], port=9042)
    session = cluster.connect('bunjang')

    # Elasticsearch 연결 설정
    es = Elasticsearch(['http://elasticsearch:9200'])

    # Cassandra에서 데이터 읽기
    rows = session.execute('SELECT * FROM products')

    # Elasticsearch에 데이터 저장
    for row in rows:
        # 가격 업데이트 정보 추출
        price_updates = [
            {
                'price': int(next(iter(item.values()))),
                'updated_at': datetime.fromtimestamp(int(next(iter(item.keys()))))
            }
            for item in row.price_updates
        ]

        # 카테고리 ID 분할
        category_id_1 = row.category_id[:3]
        category_id_2 = row.category_id[:6]
        category_id_3 = row.category_id

        # Elasticsearch에 데이터 저장
        doc = {
            'pid': row.pid,
            'brands': row.brands,
            'category_id_1': category_id_1,
            'category_id_2': category_id_2,
            'category_id_3': category_id_3,
            'name': row.name,
            'price_updates': price_updates,
            'product_image': row.product_image,
            'status': row.status
        }
        es.index(index='bunjang_products', body=doc)

    print("Data 이동 완료")

transfer_data_task = PythonOperator(
   task_id='transfer_data',
   python_callable=transfer_data,
   dag=dag,
)