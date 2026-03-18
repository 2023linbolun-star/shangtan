"""测试 1688 商品详情接口 - 用真实商品ID"""

import asyncio
import hashlib
import hmac
import json
import time

import httpx

APP_KEY = "7511345"
APP_SECRET = "i8fD4u95qn0"
ACCESS_TOKEN = "2ac71c95-4bf5-4d7f-b238-4e7b319bb4f5"

BASE_URL = "https://gw.open.1688.com/openapi/"


def sign(api_path: str, params: dict) -> str:
    sorted_params = sorted(params.items())
    sign_str = api_path + "".join(f"{k}{v}" for k, v in sorted_params)
    return hmac.new(
        APP_SECRET.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha1,
    ).hexdigest().upper()


async def call_api(api_namespace: str, api_name: str, version: str, params: dict, label: str):
    api_path = f"param2/{version}/{api_namespace}/{api_name}/{APP_KEY}"
    url = BASE_URL + api_path

    base_params = {
        "access_token": ACCESS_TOKEN,
        "_aop_timestamp": str(int(time.time() * 1000)),
    }
    base_params.update(params)
    base_params["_aop_signature"] = sign(api_path, base_params)

    print(f"\n{'='*60}")
    print(f"测试: {label}")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=base_params, timeout=15)
        print(f"HTTP 状态码: {resp.status_code}")
        data = resp.json()
        output = json.dumps(data, ensure_ascii=False, indent=2)
        print(output[:3000])
        if len(output) > 3000:
            print(f"\n... (共 {len(output)} 字符，已截断)")


async def main():
    product_id = "618610058328"

    # 1. 获取商品详情
    await call_api(
        "com.alibaba.product", "alibaba.product.get", "1",
        {"productID": product_id, "needDetail": "true", "needFreight": "true"},
        f"获取商品详情 (ID: {product_id})"
    )

    # 2. 批量获取
    await call_api(
        "com.alibaba.product", "alibaba.product.getByIdList", "1",
        {"productIdList": json.dumps([int(product_id)])},
        f"批量获取商品 (ID: {product_id})"
    )


if __name__ == "__main__":
    asyncio.run(main())
