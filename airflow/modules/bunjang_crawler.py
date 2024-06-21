# bunjang_crawler.py

import requests
import json
import os
from datetime import datetime, timedelta

def send_api_request(brands, category_id, page):
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
    print(f"API 요청 (페이지 {page + 1}): {response.url}")
    data = response.json()
    no_result = data["no_result"]
    total_count = data["categories"][0]["count"]
    return data, no_result, total_count

def parse_product_data(products, brands):
    product_list = []
    for product in products:
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
    return product_list

def get_product_list(brands, category_id, page):
    data, _, _ = send_api_request(brands, category_id, page)
    products = data["list"]
    product_list = parse_product_data(products, brands)
    return product_list

def update_products(all_products, new_products):
    all_products_dict = {product["pid"]: product for product in all_products}

    for new_product in new_products:
        pid = new_product["pid"]
        if pid in all_products_dict:
            product = all_products_dict[pid]

            if new_product["status"] != product["status"]:
                product["status"] = new_product["status"]

            new_update_time = list(new_product["price_updates"][0].keys())[0]
            if new_update_time not in [list(p.keys())[0] for p in product["price_updates"]]:
                product["price_updates"].insert(0, {
                    new_update_time: list(new_product["price_updates"][0].values())[0]
                })

            for brand in new_product["brands"]:
                if brand not in product["brands"]:
                    product["brands"].append(brand)
        else:
            all_products_dict[pid] = new_product

    return list(all_products_dict.values())

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

def collect_and_filter_data(brands, output_file):
    filtered_products = []

    data, _, _ = send_api_request(brands, 320, 0)
    top_level_categories = data["categories"]
    filtered_categories = [{"id": top_level_categories[0]["id"], "count": top_level_categories[0]["count"]}]

    total_count = filtered_categories[0]["count"]
    print(f"브랜드 {brands[0]} - 전체 제품 수: {total_count}")

    for category in filtered_categories[1:]:
        category_id = category["id"]
        page = 0
        while True:
            print(f"{page + 1} 페이지 데이터 수집 중...")
            data, no_result, total_count = send_api_request(brands, category_id, page)

            if no_result:
                break

            products = data["list"]
            collected_products = parse_product_data(products, brands)
            filtered_products.extend(filter_products(collected_products, brands[0]))

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
