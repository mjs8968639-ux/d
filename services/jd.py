"""
京东平台服务。
优先真实 API；若配置不完整或请求失败则回退到模拟数据。
"""
from __future__ import annotations

import random
from typing import List

from models import Product
from services.platform_adapters import get_platform_api_spec
from services.platform_client import PlatformRequestSpec, build_signed_params, debug_get, send_get

JD_SPEC = PlatformRequestSpec(
    base_url="https://api.jd.com/routerjson",
    method_param="method",
    sign_style="jd",
    sign_secret_env="JD_SECRET_KEY",
    app_key_env="JD_APP_KEY",
)


async def search_jd(keyword: str, page: int, page_size: int) -> List[Product]:
    try:
        return _search_jd_real(keyword, page, page_size)
    except Exception:
        return _search_jd_mock(keyword, page, page_size)


async def debug_jd_request(action: str, keyword: str | None = None, goods_id: str | None = None) -> dict:
    spec = get_platform_api_spec("jd")
    if action == "detail":
        params = build_signed_params(JD_SPEC, spec.detail, {"skuIds": goods_id or keyword or ""})
        return debug_get(JD_SPEC.base_url, params)
    if action == "search":
        params = build_signed_params(JD_SPEC, spec.search, {"skuIds": keyword or goods_id or "", "pageNo": 1, "pageSize": 10})
        return debug_get(JD_SPEC.base_url, params)
    if action == "promotion":
        return await generate_jd_promotion_url(goods_id or keyword or "")
    return {"ok": False, "error": f"不支持的京东 debug action：{action}"}


async def get_jd_detail(sku_ids: str) -> dict:
    try:
        spec = get_platform_api_spec("jd")
        params = build_signed_params(JD_SPEC, spec.detail, {"skuIds": sku_ids})
        return send_get(JD_SPEC.base_url, params)
    except Exception:
        return {"skuIds": sku_ids}


async def generate_jd_promotion_url(sku_ids: str) -> dict:
    try:
        spec = get_platform_api_spec("jd")
        params = build_signed_params(JD_SPEC, spec.promotion, {"skuIds": sku_ids})
        return send_get(JD_SPEC.base_url, params)
    except Exception:
        return {"skuIds": sku_ids, "promotion_url": f"https://item.jd.com/{sku_ids}.html"}


async def get_jd_orders(page_no: int | None = None) -> dict:
    try:
        spec = get_platform_api_spec("jd")
        params = build_signed_params(JD_SPEC, spec.order, {"pageNo": page_no or 1})
        return send_get(JD_SPEC.base_url, params)
    except Exception:
        return {"orders": []}


def _search_jd_real(keyword: str, page: int, page_size: int) -> List[Product]:
    spec = get_platform_api_spec("jd")
    params = build_signed_params(JD_SPEC, spec.search, {"skuIds": keyword, "pageNo": page, "pageSize": page_size})
    response = send_get(JD_SPEC.base_url, params)
    items = _extract_items(response)
    return [_to_product(item, keyword, i, "jd") for i, item in enumerate(items)]


def _extract_items(data: object) -> List[dict]:
    if isinstance(data, dict):
        for key in ("data", "goodsList", "items", "result"):
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
    goods_id = str(item.get("skuId") or item.get("sku_id") or item.get("id") or f"jd_{index}")
    title = str(item.get("skuName") or item.get("title") or f"【京东】{keyword} 商品 {index + 1}")
    price = float(item.get("wlPrice") or item.get("price") or 0)
    original_price = float(item.get("marketPrice") or item.get("original_price") or price)
    sales = int(item.get("inOrderCount30Days") or item.get("sales") or 0)
    image_url = str(item.get("imageUrl") or item.get("image") or "https://via.placeholder.com/300x300?text=JD")
    detail_url = str(item.get("materialUrl") or item.get("url") or f"https://item.jd.com/{goods_id}.html")
    shop_name = str(item.get("shopName") or item.get("shop_name") or "京东自营")
    tags = ["京东"]
    if item.get("categoryName"):
        tags.append(str(item.get("categoryName")))
    return Product(id=goods_id, title=title, price=price, original_price=original_price, platform=platform, image_url=image_url, sales=sales, detail_url=detail_url, shop_name=shop_name, tags=tags)


def _search_jd_mock(keyword: str, page: int, page_size: int) -> List[Product]:
    base_id = (page - 1) * page_size
    products = []
    for i in range(page_size):
        price = round(random.uniform(60, 600), 2)
        original_price = round(price * random.uniform(1.15, 1.4), 2)
        sales = random.randint(200, 80000)
        products.append(Product(id=f"jd_{base_id + i}", title=f"【京东自营】{keyword} 京东配送 品质保证 {i+1}", price=price, original_price=original_price, platform="jd", image_url="https://via.placeholder.com/300x300?text=JD", sales=sales, detail_url=f"https://search.jd.com/Search?keyword={keyword}&page={page}", shop_name=f"京东自营旗舰店{i+1}", tags=["京东", "自营", "正品"]))
    return products
