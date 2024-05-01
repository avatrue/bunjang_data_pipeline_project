import requests
from urllib.parse import quote
import json
import os
import threading
import time


def get_total_count(brands, category_id):
    base_url = "https://api.bunjang.co.kr/api/1/find_v2.json"
    params = {
        "q": brands[0],
        "order": "score",
        "page": 0,
        "f_category_id": category_id,
        "n": 100,
        "stat_category_required": 1
    }

    response = requests.get(base_url, params=params)
    print(f"전체 제품 수 조회 API: {response.url}")
    data = response.json()

    total_count = data["categories"][0]["count"]
    return total_count

def get_product_data(brands, category_id, page):
    base_url = "https://api.bunjang.co.kr/api/1/find_v2.json"
    params = {
        "q": brands[0],
        "order": "score",
        "page": page,
        "f_category_id": category_id,
        "n": 100,
        "stat_category_required": 1
    }

    response = requests.get(base_url, params=params)
    print(f"제품 데이터 조회 API (페이지 {page + 1}): {response.url}")
    data = response.json()

    product_list = []
    for product in data["list"]:
        price = product["price"]
        product_info = {
            "pid": product["pid"],
            "brands": [brand for brand in brands if brand in product["name"]],
            "name": product["name"],
            "price_updates": [{product["update_time"]: price}],
            "product_image": product["product_image"],
            "status": product["status"],
            "category_id": product["category_id"]
        }
        product_list.append(product_info)

    return data["no_result"], data["categories"][0]["count"], data["list"], product_list


def update_products(all_products, new_products):
    for new_product in new_products:
        for product in all_products:
            if product["pid"] == new_product["pid"]:
                if new_product["status"] != product["status"]:
                    product["status"] = new_product["status"]

                new_update_time = list(new_product["price_updates"][0].keys())[0]
                if new_update_time not in [list(p.keys())[0] for p in product["price_updates"]]:
                    product["price_updates"].insert(0, {
                        new_update_time: list(new_product["price_updates"][0].values())[0]})

                for brand in new_product["brands"]:
                    if brand not in product["brands"]:
                        product["brands"].append(brand)

                break
        else:
            all_products.append(new_product)

    return all_products
def get_updated_products(yesterday_data, today_data):
    updated_data = []

    for today_product in today_data:
        for yesterday_product in yesterday_data:
            if today_product["pid"] == yesterday_product["pid"]:
                if (
                    today_product["status"] != yesterday_product["status"] or
                    today_product["price_updates"][0] != yesterday_product["price_updates"][0] or
                    set(today_product["brands"]) != set(yesterday_product["brands"])
                ):
                    updated_data.append(today_product)
                break
        else:
            updated_data.append(today_product)

    return updated_data
def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def extract_categories(categories, threshold=30000, include_parent=False):
    result = []
    for category in categories:
        if category["count"] > threshold:
            if include_parent:
                result.append({"id": category["id"], "count": category["count"]})
            if "categories" in category:
                result.extend(extract_categories(category["categories"], threshold, False))
        else:
            result.append({"id": category["id"], "count": category["count"]})
    return result

def collect_and_filter_data(brands, output_file):
    filtered_products = []

    base_url = "https://api.bunjang.co.kr/api/1/find_v2.json"
    params = {
        "q": brands[0],
        "order": "score",
        "page": 0,
        "f_category_id": 320,
        "n": 100,
        "stat_category_required": 1
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    top_level_categories = data["categories"]
    filtered_categories = [{"id": top_level_categories[0]["id"], "count": top_level_categories[0]["count"]}]
    filtered_categories.extend(extract_categories(top_level_categories, include_parent=False))

    total_count = filtered_categories[0]["count"]
    print(f"브랜드 {brands[0]} - 전체 제품 수: {total_count}")

    for category in filtered_categories[1:]:
        category_id = category["id"]
        page = 0
        while True:
            print(f"{page + 1} 페이지 데이터 수집 중...")
            no_result, total_count, products, collected_products = get_product_data(brands, category_id, page)
            filtered_products.extend(filter_products(collected_products, brands[0]))

            if no_result:
                break

            page += 1
            if page == 300:
                break

    save_to_json(filtered_products, output_file)
    print(f"브랜드 {brands[0]} - 필터링 후 남은 제품 수: {len(filtered_products)}")
    print()

def filter_products(products, brand_name):
    filtered_products = []
    for product in products:
        price_updates = product["price_updates"]
        latest_price = list(price_updates[0].values())[0]
        if brand_name in product["name"] and latest_price.isdigit() and latest_price[-1] == "0" and int(latest_price) >= 10000:
            product["brands"] = [brand_name]
            filtered_products.append(product)
    return filtered_products







def merge_results(input_dir, output_file, lock, brand):
    print(f"Input directory: {input_dir}")
    print(f"Output file: {output_file}")
    print(f"Merging data for brand: {brand}")

    all_products = []

    # 기존 파일이 있는 경우 읽어옴
    if os.path.exists(output_file):
        print(f"Reading existing file: {output_file}")
        with open(output_file, "r", encoding="utf-8") as file:
            lock.acquire()
            try:
                all_products = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Failed to parse existing file: {e}")
                all_products = []
            finally:
                lock.release()
    else:
        print(f"Creating new file: {output_file}")

    # 특정 브랜드 파일 읽어와서 병합
    brand_file = os.path.join(input_dir, f"{brand}_products.json")
    print(f"Reading brand file: {brand_file}")
    with open(brand_file, "r", encoding="utf-8") as file:
        try:
            brand_products = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Failed to parse brand file: {brand_file}, error: {e}")
            brand_products = []

        # 기존 데이터와 중복되지 않는 제품만 추가
        for product in brand_products:
            if product not in all_products:
                all_products.append(product)

    # 병합된 데이터를 파일로 저장
    print(f"Saving merged data to: {output_file}")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as file:
        lock.acquire()
        try:
            json.dump(all_products, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to save merged data: {e}")
        finally:
            lock.release()

    print(f"Merge completed for brand: {brand}")