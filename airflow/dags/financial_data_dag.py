from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from pytz import timezone
import logging
import sys
import json
import os

sys.path.append("/opt/airflow/modules")

from exchange_rate_fetcher import ExchangeRateFetcher
from nasdaq_data_fetcher import NasdaqDataFetcher


def fetch_financial_data(**kwargs) -> None:
    api_key = "QFenQjzBrzZixROTFHyY5QN2IMkUmZ0e"
    nasdaq_ticker = "^IXIC"

    execution_date = kwargs["execution_date"]

    exchange_fetcher = ExchangeRateFetcher(api_key)
    nasdaq_fetcher = NasdaqDataFetcher(nasdaq_ticker)

    usd_exchange_rate = exchange_fetcher.get_usd_exchange_rate()
    nasdaq_data = nasdaq_fetcher.get_nasdaq_data(execution_date)

    usd = usd_exchange_rate.split(".")[0]
    nasdaq = str(nasdaq_data["Close"].iloc[-1]).split(".")[0]

    data = {
        "date": execution_date.strftime("%Y%m%d"),
        "usd": usd.replace(",", ""),
        "nasdaq": nasdaq,
    }

    output_path = "/opt/airflow/output/financial_data.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as file:
        json.dump(data, file)

    logging.info(f"Data saved as json: {data}")


# Logging 설정
logging.basicConfig(level=logging.INFO)

KST = timezone("Asia/Seoul")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 4, 1, 18, 0, 0, tzinfo=KST),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "financial_data_download",
    default_args=default_args,
    description="Download financial data daily at 6 PM KST",
    schedule_interval="0 18 * * *",  # 매일 오후 6시에 실행
    catchup=False,
)

fetch_data_task = PythonOperator(
    task_id="fetch_financial_data",
    python_callable=fetch_financial_data,
    dag=dag,
    provide_context=True,
)

fetch_data_task
