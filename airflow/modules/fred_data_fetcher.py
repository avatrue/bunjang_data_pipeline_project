from fredapi import Fred
import logging
from datetime import datetime, timedelta
import os


class FredDataFetcher:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def get_data(self, series_id: str, date: datetime) -> float:
        data = self.fred.get_series(
            series_id, observation_start=date, observation_end=date
        )
        if not data.empty:
            return float(data.iloc[0])
        return None

    def get_previous_data(self, series_id: str, date: datetime) -> float:
        while True:
            date -= timedelta(days=1)
            previous_date = date.strftime("%Y-%m-%d")
            data = self.fred.get_series(
                series_id,
                observation_start=previous_date,
                observation_end=previous_date,
            )
            if not data.empty:
                return float(data.iloc[0])
        return None

    def get_cpi_data(self, date: datetime) -> float:
        return int(self.get_data("CPIAUCSL", date))

    def get_unrate_data(self, date: datetime) -> float:
        return self.get_data("UNRATE", date)

    def get_payems_data(self, date: datetime) -> float:
        return int(self.get_data("PAYEMS", date))

    def get_permit_data(self, date: datetime) -> float:
        return int(self.get_data("PERMIT", date))

    def get_umcsent_data(self, date: datetime) -> float:
        return self.get_data("UMCSENT", date)


if __name__ == "__main__":
    fetcher = FredDataFetcher()
    date = datetime(2023, 1, 1)
    cpi_data = fetcher.get_cpi_data(date)
    unrate_data = fetcher.get_unrate_data(date)
    payems_data = fetcher.get_payems_data(date)
    permit_data = fetcher.get_permit_data(date)
    umcsent_data = fetcher.get_umcsent_data(date)

    print("CPI Data:", cpi_data)
    print("Unemployment Rate Data:", unrate_data)
    print("Nonfarm Payroll Data:", payems_data)
    print("Building Permits Data:", permit_data)
    print("Consumer Sentiment Data:", umcsent_data)
