import requests
import logging
import pytz
from datetime import datetime, timedelta


class ExchangeRateFetcher:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def get_usd_exchange_rate(self) -> str:
        utc_now = datetime.now(pytz.utc)
        search_date = utc_now.strftime("%Y-%m-%d")
        url = (
            f"https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
            f"?authkey={self.api_key}&searchdate={search_date}&data=AP01"
        )

        logging.info(f"Requesting USD exchange rate for {search_date}")
        response = requests.get(url)
        logging.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            usd = [i for i in data if i["cur_unit"] == "USD"]
            if usd:
                return usd[0]["deal_bas_r"]
            else:
                return self.get_previous_usd_exchange_rate(utc_now)
        else:
            return f"Failed to request data: {response.status_code}"

    def get_previous_usd_exchange_rate(self, date: datetime) -> str:
        while True:
            date -= timedelta(days=1)
            search_date = date.strftime("%Y-%m-%d")
            url = (
                f"https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
                f"?authkey={self.api_key}&searchdate={search_date}&data=AP01"
            )
            logging.info(f"Requesting previous USD exchange rate for {search_date}")
            response = requests.get(url)
            logging.info(f"Response status code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                usd = [i for i in data if i["cur_unit"] == "USD"]
                if usd:
                    return usd[0]["deal_bas_r"]
