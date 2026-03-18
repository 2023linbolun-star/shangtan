"""测试各平台 API 是否能正常返回数据"""

import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path

# 加载 .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ[key.strip()] = value.strip()

import httpx


async def test_pinduoduo(keyword: str = "瑜伽裤"):
    print(f"\n{'='*60}")
    print(f"测试平台: 拼多多（多多进宝）")
    print(f"{'='*60}")

    client_id = os.environ.get("PDD_CLIENT_ID", "")
    client_secret = os.environ.get("PDD_CLIENT_SECRET", "")

    params = {
        "type": "pdd.ddk.goods.search",
        "client_id": client_id,
        "timestamp": str(int(time.time())),
        "data_type": "JSON",
        "keyword": keyword,
        "page": 1,
        "page_size": 10,
        "sort_type": 0,
        "pid": "44173417_314741089",
        "custom_parameters": '{"uid":"shangtanai","new":1}',
    }

    sorted_params = sorted(params.items())
    sign_str = client_secret + "".join(f"{k}{v}" for k, v in sorted_params) + client_secret
    params["sign"] = hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://gw-api.pinduoduo.com/api/router", json=params, timeout=15)
        data = resp.json()

        if "error_response" in data:
            print(f"❌ 错误: {data['error_response'].get('sub_msg', data['error_response'].get('error_msg'))}")
            print(f"原始响应:\n{json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            return

        search_resp = data.get("goods_search_response", {})
        goods_list = search_resp.get("goods_list", [])
        total = search_resp.get("total_count", 0)
        print(f"✅ 搜索成功！共 {total} 个商品，返回 {len(goods_list)} 个\n")

        # 打印第一个商品的完整字段
        if goods_list:
            print("第一个商品完整字段:")
            print(json.dumps(goods_list[0], ensure_ascii=False, indent=2)[:1500])
            print()

        for i, item in enumerate(goods_list[:5], 1):
            price = item.get("min_group_price", 0) / 100
            sales = item.get("sold_quantity", item.get("sales_tip", "未知"))
            rate = item.get("promotion_rate", 0) / 1000 * 100
            print(f"  {i}. {item.get('goods_name', '')[:45]}")
            print(f"     价格: ¥{price:.2f}  |  销量: {sales}  |  佣金率: {rate:.1f}%  |  店铺: {item.get('mall_name', '')}")
            print()


async def test_douyin(keyword: str = "瑜伽裤"):
    print(f"\n{'='*60}")
    print(f"测试平台: 抖音（聚推客）")
    print(f"{'='*60}")

    params = {
        "pub_id": "456701",
        "title": keyword,
        "page": 1,
        "page_size": 5,
        "search_type": 0,
        "sort_type": 1,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.act.jutuike.com/dyfx/product_search", params=params, timeout=15)
        data = resp.json()

        if data.get("code") != 0 and data.get("msg") != "success":
            print(f"❌ 错误: {data.get('msg', '未知错误')}")
            print(f"原始响应:\n{json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            return

        goods_list = data.get("data", [])
        if not goods_list:
            print("⚠️ 搜索成功但无结果")
            print(f"原始响应:\n{json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            return

        print(f"✅ 搜索成功！返回 {len(goods_list)} 个商品\n")

        for i, item in enumerate(goods_list[:5], 1):
            price = item.get("price", 0) / 100  # 分→元
            sales = item.get("sales", "未知")
            cos_ratio = item.get("cos_ratio", 0)
            cos_fee = item.get("cos_fee", 0) / 100  # 分→元
            title = item.get("title", "")
            shop = item.get("shop_name", "")
            print(f"  {i}. {title[:45]}")
            print(f"     价格: ¥{price:.2f}  |  销量: {sales}  |  佣金率: {cos_ratio}%  |  佣金: ¥{cos_fee:.2f}  |  店铺: {shop}")
            print()


async def main():
    keyword = sys.argv[1] if len(sys.argv) > 1 else "瑜伽裤"
    await test_pinduoduo(keyword)
    await test_douyin(keyword)


if __name__ == "__main__":
    asyncio.run(main())
