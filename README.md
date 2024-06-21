# 번개장터 제품 배치 파이프라인

이 프로젝트는 번개장터라는 사이트의 중고제품을 크롤링하고, 브랜드별로 데이터를 집계하며 시세를 추적하는 데이터 파이프라인입니다. 이를 통해 사용자들은 중고 제품의 시세 변동을 쉽게 파악하고, 거래에 유용한 정보를 얻을 수 있습니다.

## 주요 기능

- **데이터 수집:** 에어플로우를 이용해 번개장터의 중고 제품 데이터를 자동으로 수집합니다.
- **데이터 처리:** 수집된 데이터를 정제하고, 브랜드별로 분류합니다.
- **시세 추적:** 시세 변동을 추적하여 데이터를 제공합니다.
- **데이터 저장:** 처리된 데이터를 데이터베이스에 저장하여 쉽게 조회할 수 있도록 합니다.

## 시작하기

이 프로젝트를 시작하려면 아래의 지침을 따르세요.

### 필수 조건

- **Docker:** 이 프로젝트는 Docker를 사용합니다. Docker가 설치되어 있어야 합니다.
- **Docker Compose:** Docker Compose가 설치되어 있어야 합니다.

### 설치

1. **프로젝트 클론:**
   ```bash
   git clone https://github.com/avatrue/bunjang_data_pipeline_project.git
   cd bunjang_data_pipeline_project

### Docker Compose 실행:
```bash
docker network create bunjang_data_pipeline_project_default
docker-compose -f docker-compose-airflow.yaml -f docker-compose-elk.yaml -f docker-compose-hadoop.yaml up
```

### 환경 설정

#### 브랜드 설정
프로젝트`의 루트 디렉토리에 있는 `data` 폴더 안의 `brands.json` 파일을 편집하여 크롤링할 브랜드를 관리합니다. 현재는 108개의 브랜드가 설정되어 있습니다. 새로운 브랜드를 추가하려면 다음 형식을 따릅니다:

```json
{
  "한글브랜드명": "영문브랜드명",
  "추가브랜드1": "영문브랜드명1",
  "추가브랜드2": "영문브랜드명2"
}
```
### 데이터 파이프라인 설명

에어플로우에서 두 가지 DAG이 돌아갑니다:

#### merge_trigger:

- 파이썬 모듈의 request로 번개장터의 API에서 브랜드별 제품 데이터를 가져옵니다.
- 각 제품별로 해당 날짜로 제품 데이터를 JSON으로 생성합니다. 예: `032c_20240402_products.json`.
- 이후 전날의 데이터와 비교하여 업데이트가 필요한 제품 데이터를 모아 JSON 파일로 만듭니다. 예: `032c_update_20240402.json`.
- 그리고 이 데이터를 merge DAG에 트리거를 날립니다.

#### merge:

- 트리거를 받으면 받은 순서대로 데이터베이스를 업데이트합니다. 원래는 S3에서 Cassandra로 바뀌었고, 현재는 Elasticsearch를 이용 중입니다.

#### 데이터 구조 예시

```json
{
    "pid": "242114787",
    "brands": ["포터리"],
    "name": "포터리 울 스포츠 셋업 미드그레이 상의3 하의4",
    "price_updates": [
        { "1713231918": "490000" },
        { "1713086700": "490000" },
        { "1712646108": "490000" },
        { "1712028723": "490000" }
    ],
    "product_image": "https://media.bunjang.co.kr/product/242114787_1_1709899870_w{res}.jpg",
    "status": "0",
    "category_id": "320500100"
}
```

### 프로젝트 구조

```plaintext
bunjang_data_pipeline_project/
├── airflow/                  # Airflow 관련 설정 파일
│   └── config/               # Airflow 구성 파일
├── dags/                     # Airflow DAG 파일
│   ├── bunjang_crawler_test_dag.py
│   ├── cassandra_to_elk_dag.py
│   ├── merge_next_v_test.py
│   ├── merge_release.py
│   ├── merge_trigger_next_v_test.py
│   ├── merge_trigger_release.py
│   └── split_merge_test.py
├── logs/                     # 로그 파일
├── modules/                  # Python 모듈
│   ├── bunjang_crawler.py
│   └── bunjang_crawler_backup.py
├── output/                   # 출력 데이터
├── cassandra/                # Cassandra 관련 파일
├── config/                   # 구성 파일
├── dags/                     # DAG 파일
├── data/                     # 데이터 파일
│   ├── brands.json
│   ├── brands_test.json
│   └── init_casandra.py
├── elasticsearch/            # Elasticsearch 관련 파일
├── output/                   # 출력 데이터
├── .env                      # 환경 변수 파일
├── .gitignore                # Git 무시 파일
├── data.zip                  # 데이터 압축 파일
├── docker-compose.yaml       # Docker Compose 파일
├── docker-compose-elk.yml    # Docker Compose ELK 스택 파일
└── requirements.txt          # Python 의존성 파일
```


