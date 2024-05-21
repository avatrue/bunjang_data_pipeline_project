import yfinance as yf
import logging
import pandas as pd
from datetime import datetime, timedelta


class NasdaqDataFetcher:
    def __init__(self, nasdaq_ticker: str) -> None:
        self.nasdaq_ticker = nasdaq_ticker

    def get_nasdaq_data(self, date: datetime) -> pd.DataFrame:
        logging.info(f"Requesting NASDAQ data for {date.strftime('%Y-%m-%d')}")
        nasdaq_data = yf.download(
            self.nasdaq_ticker,
            start=date.strftime("%Y-%m-%d"),
            end=(date + timedelta(days=1)).strftime("%Y-%m-%d"),
        )

        nasdaq_data = nasdaq_data[nasdaq_data.index.date == date.date()]

        if nasdaq_data.empty:
            return self.get_previous_nasdaq_data(date)
        return nasdaq_data

    def get_previous_nasdaq_data(self, date: datetime) -> pd.DataFrame:
        while True:
            date -= timedelta(days=1)
            previous_date = date.strftime("%Y-%m-%d")
            logging.info(f"Requesting previous NASDAQ data for {previous_date}")
            nasdaq_data = yf.download(
                self.nasdaq_ticker,
                start=previous_date,
                end=(date + timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            if not nasdaq_data.empty:
                return nasdaq_data
