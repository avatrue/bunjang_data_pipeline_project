import json
import tweepy
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

class TwitterBrandMentions:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.load_env_variables()  # 환경 변수를 로드하는 메서드 호출
        self.api = self.setup_twitter_api()
        self.brands = self.read_json()

    def load_env_variables(self):
        # 현재 파일의 디렉토리 경로
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 두 디렉토리 위로 이동
        env_path = os.path.join(current_dir, '..', '..', '.env')
        load_dotenv(dotenv_path=env_path)  # 지정된 경로에서 .env 파일을 로드해

        self.api_key = os.getenv('API_KEY')
        self.api_key_secret = os.getenv('API_KEY_SECRET')
        self.access_token = os.getenv('ACCESS_TOKEN')
        self.access_token_secret = os.getenv('ACCESS_TOKEN_SECRET')

        # 환경 변수가 제대로 로드되었는지 확인 (디버깅용, 5필요 시 제거)
        if not all([self.api_key, self.api_key_secret, self.access_token, self.access_token_secret]):
            raise EnvironmentError("Some environment variables are missing. Please check your .env file.")

    def setup_twitter_api(self):
        auth = tweepy.OAuthHandler(self.api_key, self.api_key_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        api = tweepy.API(auth)
        return api

    def read_json(self):
        with open(self.json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def search_tweets(self, query, date_since, date_until):
        tweets = tweepy.Cursor(self.api.search_tweets,
                               q=query,
                               lang='ko',
                               since=date_since,
                               until=date_until).items()
        return [tweet.text for tweet in tweets]

    def get_brand_mentions(self, date_since):
        date_until = (datetime.strptime(date_since, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        results = {}
        for korean_name, english_name in self.brands.items():
            print(f"Searching for {korean_name} ({english_name})...")

            korean_tweets = self.search_tweets(korean_name, date_since, date_until)
            english_tweets = self.search_tweets(english_name, date_since, date_until)

            results[korean_name] = {
                "korean_tweets": len(korean_tweets),
                "english_tweets": len(english_tweets)
            }

        return results


# 테스트 코드
if __name__ == "__main__":
    json_file_path = 'brands.json'  # JSON 파일 경로를 지정해줘
    date_since = '2023-06-13'  # 원하는 시작 날짜를 지정해줘

    tbm = TwitterBrandMentions(json_file_path)
    results = tbm.get_brand_mentions(date_since)

    for brand, counts in results.items():
        print(f"{brand}: {counts}")
