# FRED에서 CPI, 미국 실업율, 미국 비농업 부문 고용인원, 건축 허가수, 미시간대학 소비자 심리지수 수집

from fredapi import Fred
import logging
from datetime import datetime, timedelta


class FredDataFetcher:
    def __init__(self, api_key: str) -> None:
        self.fred = Fred(api_key=api_key)

    def get_data(self, series_id: str, date: datetime) -> float:
        try:
            # 해당 월의 1일부터 입력된 날짜까지 데이터를 검색
            start_date = date.replace(day=1).strftime("%Y-%m-%d")
            end_date = date.strftime("%Y-%m-%d")
            data = self.fred.get_series(series_id, start_date, end_date)

            # 최신 데이터 확인
            if not data.empty:
                latest_data = data.iloc[-1]
                return latest_data

            # 해당 월에 데이터가 없으면 이전 월로 이동
            return self.get_previous_data(series_id, date)

        except Exception as e:
            logging.error(f"Failed to fetch data for series {series_id}: {e}")
            return float("nan")

    def get_previous_data(self, series_id: str, date: datetime) -> float:
        max_attempts = 3  # 최대 3개월 전까지 시도
        while max_attempts > 0:
            # 이전 달의 마지막 날로 이동
            date = date.replace(day=1) - timedelta(days=1)
            start_date = date.replace(day=1).strftime("%Y-%m-%d")
            end_date = date.strftime("%Y-%m-%d")
            logging.info(
                f"Requesting previous data for {series_id} from {start_date} to {end_date}"
            )
            data = self.fred.get_series(series_id, start_date, end_date)

            # 최신 데이터 확인
            if not data.empty:
                latest_data = data.iloc[-1]
                return latest_data

            max_attempts -= 1

        logging.error(
            f"No data found for series {series_id} in the past 12 months from {date.strftime('%Y-%m-%d')}"
        )
        return float("nan")

    def get_cpi_data(self, date: datetime) -> float:
        return self.get_data("CPIAUCSL", date)

    def get_unrate_data(self, date: datetime) -> float:
        return self.get_data("UNRATE", date)

    def get_payems_data(self, date: datetime) -> float:
        return self.get_data("PAYEMS", date)

    def get_permit_data(self, date: datetime) -> float:
        return self.get_data("PERMIT", date)

    def get_umcsent_data(self, date: datetime) -> float:
        return self.get_data("UMCSENT", date)
