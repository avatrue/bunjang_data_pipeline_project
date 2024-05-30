# 금융, 경제 관련 데이터 Dag

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from pytz import timezone
import logging
import sys
import json
import os
import happybase
from dotenv import load_dotenv

load_dotenv(dotenv_path="/opt/.env")
sys.path.append("/opt/airflow/modules")

from exchange_rate_fetcher import ExchangeRateFetcher
from yfinance_data_fetcher import YfinanceDataFetcher
from fred_data_fetcher import FredDataFetcher


def fetch_financial_data(**kwargs) -> None:
    EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")
    FRED_API_KEY = os.getenv("FRED_API_KEY")
    HBASE_HOST = os.getenv("HBASE_HOST")

    execution_date = kwargs["execution_date"]

    exchange_fetcher = ExchangeRateFetcher(EXCHANGE_API_KEY)
    fred_fetcher = FredDataFetcher(FRED_API_KEY)
    yfinance_fetcher = YfinanceDataFetcher()

    usd = exchange_fetcher.get_usd_exchange_rate()
    nasdaq = yfinance_fetcher.get_nasdaq_data(execution_date)
    kospi = yfinance_fetcher.get_kospi_data(execution_date)
    kosdaq = yfinance_fetcher.get_kosdaq_data(execution_date)
    cpi = fred_fetcher.get_cpi_data(execution_date)
    unrate = fred_fetcher.get_unrate_data(execution_date)
    payems = fred_fetcher.get_payems_data(execution_date)
    permit = fred_fetcher.get_permit_data(execution_date)
    umcsent = fred_fetcher.get_umcsent_data(execution_date)

    nasdaq_close = nasdaq["Close"].iloc[-1]
    kospi_close = kospi["Close"].iloc[-1]
    kosdaq_close = kosdaq["Close"].iloc[-1]

    data = {
        "date": execution_date.strftime("%Y%m%d"),
        "usd": usd,
        "nasdaq": nasdaq_close,
        "kospi": kospi_close,
        "kosdaq": kosdaq_close,
        "cpi": cpi,
        "unrate": unrate,
        "payems": payems,
        "permit": permit,
        "umcsent": umcsent,
    }

    output_path = "/opt/airflow/output/financial_data.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as file:
        json.dump(data, file)

    logging.info(f"Data saved as json: {data}")

    # db connection
    connection = happybase.Connection(HBASE_HOST)
    table = connection.table('financial_data')
    table.put(data["date"], {f'data:{k}': str(v) for k, v in data.items()})

    logging.info(f"Data saved to HBase: {data}")


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
