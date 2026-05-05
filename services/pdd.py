"""
拼多多平台服务。
优先真实 API；若配置不完整或请求失败则回退到模拟数据。
"""
from __future__ import annotations

import random
from typing import List

from models import Product
from services.platform_adapters import get_platform_api_spec
from services.platform_client import PlatformRequestSpec, build_signed_params, send_post

PDD_SPEC = PlatformRequestSpec(
    base_url="https://gw-api.pinduoduo.com/api/router",
    method_param="type",
    sign_style="pdd",
    sign_secret_env="PDD_CLIENT_SECRET",
    app_key_env="PDD_CLIENT_ID",
)


async def search_pdd(keyword: str, page: int, page_size: int) -> List[Product]:
    try:
        return _search_pdd_real(keyword, page, page_size)
    except Exception:
        return _search_pdd_mock(keyword, page, page_size)


async def get_pdd_detail(goods_id: str) -> dict:
    try:
        spec = get_platform_api_spec("pdd")
        params = build_signed_params(PDD_SPEC, spec.detail, {"goods_id_list": goods_id})
        return send_post(PDD_SPEC.base_url, params)
    except Exception:
        return {"goods_id": goods_id}


async def generate_pdd_promotion_url(goods_id: str, pid: str | None = None) -> dict:
    try:
        spec = get_platform_api_spec("pdd")
        params = build_signed_params(
            PDD_SPEC,
            spec.promotion,
            {
                "goods_id_list": goods_id,
                "p_id": pid or "",
                "pid": pid or "",
            },
        )
        return send_post(PDD_SPEC.base_url, params)
    except Exception:
        return {"goods_id": goods_id, "promotion_url": f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}"}


async def get_pdd_orders(last_order_id: str | None = None) -> dict:
    try:
        spec = get_platform_api_spec("pdd")
        params = build_signed_params(PDD_SPEC, spec.order, {"last_order_id": last_order_id or ""})
        return send_post(PDD_SPEC.base_url, params)
    except Exception:
        return {"orders": []}


def _search_pdd_real(keyword: str, page: int, page_size: int) -> List[Product]:
    spec = get_platform_api_spec("pdd")
    params = build_signed_params(
        PDD_SPEC,
        spec.search,
        {
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
        },
    )
    response = send_post(PDD_SPEC.base_url, params)
    items = _extract_items(response)
    return [_to_product(item, keyword, i, "pdd") for i, item in enumerate(items)]


def _extract_items(data: object) -> List[dict]:
    if isinstance(data, dict):
        for key in ("goods_list", "items", "result", "goods_details"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        for value in data.values():
            if isinstance(value, dict):
                nested = _extract_items(value)
                if nested:
                    return nested
    return []


def _to_product(item: dict, keyword: str, index: int, platform: str) -> Product:
    goods_id = str(item.get("goods_id") or item.get("goodsId") or item.get("sku_id") or f"pdd_{index}")
    title = str(item.get("goods_name") or item.get("goodsName") or item.get("title") or f"【拼多多】{keyword} 商品 {index + 1}")
    raw_price = item.get("min_group_price") or item.get("promotion_price") or item.get("price") or 0
    price = float(raw_price) / 100 if isinstance(raw_price, (int, float)) and float(raw_price) > 1000 else float(raw_price)
    original = item.get("market_price") or item.get("original_price") or item.get("price")
    original_price = float(original) / 100 if isinstance(original, (int, float)) and float(original) > 1000 else float(original) if original is not None else None
    sales = int(item.get("sales_tip") or item.get("sales") or item.get("sold_quantity") or 0)
    image_url = str(item.get("goods_image_url") or item.get("image_url") or item.get("image") or "https://via.placeholder.com/300x300?text=PDD")
    detail_url = str(item.get("detail_url") or item.get("url") or f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}")
    shop_name = str(item.get("mall_name") or item.get("shop_name") or item.get("merchant_name") or "拼多多商家")
    tags = ["拼多多"]
    if item.get("cat_name"):
        tags.append(str(item.get("cat_name")))
    return Product(id=goods_id, title=title, price=price, original_price=original_price, platform=platform, image_url=image_url, sales=sales, detail_url=detail_url, shop_name=shop_name, tags=tags)


def _search_pdd_mock(keyword: str, page: int, page_size: int) -> List[Product]:
    base_id = (page - 1) * page_size
    products = []
    for i in range(page_size):
        price = round(random.uniform(30, 300), 2)
        original_price = round(price * random.uniform(1.3, 1.8), 2)
        sales = random.randint(500, 100000)
        products.append(Product(id=f"pdd_{base_id + i}", title=f"【拼多多】{keyword} 限时特价 包邮到家 {i+1}", price=price, original_price=original_price, platform="pdd", image_url="https://via.placeholder.com/300x300?text=PDD", sales=sales, detail_url=f"https://mobile.yangkeduo.com/search_result.html?search_key={keyword}", shop_name=f"拼多多商家{i+1}", tags=["拼多多", "特价", "包邮"]))
    return products
