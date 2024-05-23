# 야후 파이낸스에서 코스피, 코스닥, 나스닥 수집

import yfinance as yf
import logging
import pandas as pd
from datetime import datetime, timedelta


class YfinanceDataFetcher:
    def __init__(self) -> None:
        self.nasdaq_ticker = "^IXIC"
        self.kospi_ticker = "^KS11"
        self.kosdaq_ticker = "^KQ11"

    def get_data(self, ticker: str, date: datetime) -> pd.DataFrame:
        logging.info(f"Requesting data for {ticker} on {date.strftime('%Y-%m-%d')}")
        market_data = yf.download(
            ticker,
            start=date.strftime("%Y-%m-%d"),
            end=(date + timedelta(days=1)).strftime("%Y-%m-%d"),
        )

        # 데이터가 없는 경우 이전 날짜로 이동
        if market_data.empty:
            return self.get_previous_data(ticker, date)
        return market_data

    def get_previous_data(self, ticker: str, date: datetime) -> pd.DataFrame:
        max_attempts = 30  # 최대 30일 동안 이전 데이터를 시도
        while max_attempts > 0:
            date -= timedelta(days=1)
            previous_date = date.strftime("%Y-%m-%d")
            logging.info(f"Requesting previous data for {ticker} on {previous_date}")
            market_data = yf.download(
                ticker,
                start=previous_date,
                end=(date + timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            logging.info(f"Previous market data: {market_data}")

            if not market_data.empty:
                return market_data

            max_attempts -= 1

        logging.error(
            f"Data not found for {ticker} in the past 30 days from {date.strftime('%Y-%m-%d')}"
        )
        return pd.DataFrame()  # 데이터가 없을 경우 빈 DataFrame 반환

    def get_nasdaq_data(self, date: datetime) -> pd.DataFrame:
        return self.get_data(self.nasdaq_ticker, date)

    def get_kospi_data(self, date: datetime) -> pd.DataFrame:
        return self.get_data(self.kospi_ticker, date)

    def get_kosdaq_data(self, date: datetime) -> pd.DataFrame:
        return self.get_data(self.kosdaq_ticker, date)
