"""
淘宝平台服务。
优先真实 API；若配置不完整或请求失败则回退到模拟数据。
"""
from __future__ import annotations

import random
from typing import List

from models import Product
from services.platform_adapters import get_platform_api_spec
from services.platform_client import PlatformRequestSpec, build_signed_params, debug_get, send_get

TAOBAO_SPEC = PlatformRequestSpec(
    base_url="https://gw.api.taobao.com/router/rest",
    method_param="method",
    sign_style="taobao",
    sign_secret_env="TAOBAO_APP_SECRET",
    app_key_env="TAOBAO_APP_KEY",
)


async def search_taobao(keyword: str, page: int, page_size: int) -> List[Product]:
    try:
        return _search_taobao_real(keyword, page, page_size)
    except Exception:
        return _search_taobao_mock(keyword, page, page_size)


async def debug_taobao_request(action: str, keyword: str | None = None, goods_id: str | None = None) -> dict:
    spec = get_platform_api_spec("taobao")
    if action == "detail":
        params = build_signed_params(TAOBAO_SPEC, spec.detail, {"num_iids": goods_id or keyword or ""})
        return debug_get(TAOBAO_SPEC.base_url, params)
    if action == "search":
        params = build_signed_params(TAOBAO_SPEC, spec.search, {"q": keyword or goods_id or "", "page_no": 1, "page_size": 10})
        return debug_get(TAOBAO_SPEC.base_url, params)
    if action == "promotion":
        return await generate_taobao_promotion_url(goods_id or keyword or "")
    return {"ok": False, "error": f"不支持的淘宝 debug action：{action}"}


async def get_taobao_detail(num_iids: str) -> dict:
    try:
        spec = get_platform_api_spec("taobao")
        params = build_signed_params(TAOBAO_SPEC, spec.detail, {"num_iids": num_iids})
        return send_get(TAOBAO_SPEC.base_url, params)
    except Exception:
        return {"num_iids": num_iids}


async def generate_taobao_promotion_url(num_iids: str, pid: str | None = None) -> dict:
    target_url = f"https://item.taobao.com/item.htm?id={num_iids}"
    try:
        spec = get_platform_api_spec("taobao")
        params = build_signed_params(
            TAOBAO_SPEC,
            spec.promotion,
            {
                "text": "商品推广",
                "url": target_url,
                "adzone_id": _extract_taobao_adzone_id(pid or ""),
            },
        )
        return send_get(TAOBAO_SPEC.base_url, params)
    except Exception:
        return {"num_iids": num_iids, "promotion_url": target_url}


def _extract_taobao_adzone_id(pid: str) -> str:
    parts = pid.split("_")
    return parts[-1] if len(parts) >= 4 else ""


async def get_taobao_orders(start_time: str | None = None) -> dict:
    try:
        spec = get_platform_api_spec("taobao")
        params = build_signed_params(TAOBAO_SPEC, spec.order, {"start_time": start_time or ""})
        return send_get(TAOBAO_SPEC.base_url, params)
    except Exception:
        return {"orders": []}


def _search_taobao_real(keyword: str, page: int, page_size: int) -> List[Product]:
    spec = get_platform_api_spec("taobao")
    params = build_signed_params(TAOBAO_SPEC, spec.search, {"q": keyword, "page_no": page, "page_size": page_size})
    response = send_get(TAOBAO_SPEC.base_url, params)
    items = _extract_items(response)
    return [_to_product(item, keyword, i, "taobao") for i, item in enumerate(items)]


def _extract_items(data: object) -> List[dict]:
    if isinstance(data, dict):
        for key in ("results", "n_tbk_item", "items", "item"):
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
    goods_id = str(item.get("num_iid") or item.get("item_id") or item.get("id") or f"tb_{index}")
    title = str(item.get("title") or item.get("item_name") or f"【淘宝】{keyword} 商品 {index + 1}")
    price_raw = item.get("zk_final_price") or item.get("price") or item.get("reserve_price") or 0
    price = float(price_raw)
    original_raw = item.get("reserve_price") or item.get("price") or None
    original_price = float(original_raw) if original_raw is not None else None
    sales = int(item.get("volume") or item.get("sales") or 0)
    image_url = str(item.get("pict_url") or item.get("image") or "https://via.placeholder.com/300x300?text=Taobao")
    detail_url = str(item.get("item_url") or item.get("url") or f"https://item.taobao.com/item.htm?id={goods_id}")
    shop_name = str(item.get("shop_title") or item.get("nick") or item.get("shop_name") or "淘宝店铺")
    tags = ["淘宝"]
    if item.get("category"):
        tags.append(str(item.get("category")))
    return Product(id=goods_id, title=title, price=price, original_price=original_price, platform=platform, image_url=image_url, sales=sales, detail_url=detail_url, shop_name=shop_name, tags=tags)


def _search_taobao_mock(keyword: str, page: int, page_size: int) -> List[Product]:
    base_id = (page - 1) * page_size
    products = []
    for i in range(page_size):
        price = round(random.uniform(50, 500), 2)
        original_price = round(price * random.uniform(1.2, 1.5), 2)
        sales = random.randint(100, 50000)
        products.append(Product(id=f"tb_{base_id + i}", title=f"【淘宝】{keyword} 正品保障 包邮 {i+1}", price=price, original_price=original_price, platform="taobao", image_url="https://via.placeholder.com/300x300?text=Taobao", sales=sales, detail_url=f"https://s.taobao.com/search?q={keyword}&s={base_id + i}", shop_name=f"淘宝店铺{i+1}", tags=["淘宝", "包邮", "正品"]))
    return products
