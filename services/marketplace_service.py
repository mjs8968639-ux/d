"""
平台聚合服务。
当前优先通过环境变量配置平台凭证；若未配置则回退到模拟数据，确保前端流程可先跑通。
"""
from __future__ import annotations

import asyncio
import os
import random
from typing import List
from urllib.parse import quote_plus

from models import Product, SearchRequest, SearchResponse
from services.platform_adapters import get_platform_api_spec
from services.taobao import debug_taobao_request, generate_taobao_promotion_url, get_taobao_detail, get_taobao_orders, search_taobao
from services.jd import debug_jd_request, generate_jd_promotion_url, get_jd_detail, get_jd_orders, search_jd
from services.pdd import debug_pdd_request, generate_pdd_promotion_url, get_pdd_detail, get_pdd_orders, search_pdd

PLATFORM_WEIGHTS = {
    "taobao": 1.0,
    "jd": 0.98,
    "pdd": 0.92,
}


def _has_platform_credentials(prefix: str) -> bool:
    return bool(
        os.getenv(f"{prefix}_APP_KEY")
        or os.getenv(f"{prefix}_CLIENT_ID")
        or os.getenv(f"{prefix}_PID")
    )


def _platform_search_url(platform: str, keyword: str) -> str:
    spec = get_platform_api_spec(platform)
    if not spec:
        return ""
    base_urls = {
        "taobao": "https://eco.taobao.com/router/rest",
        "jd": "https://router.jd.com/api",
        "pdd": "https://gw-api.pinduoduo.com/api/router",
    }
    base_url = base_urls.get(platform.lower().strip(), "")
    if not base_url:
        return ""
    return f"{base_url}?method={quote_plus(spec.search)}&keyword={quote_plus(keyword)}"


async def search_platform(keyword: str, page: int, page_size: int, platform: str) -> List[Product]:
    platform = platform.lower().strip()
    if platform == "taobao":
        return await search_taobao(keyword, page, page_size)
    if platform == "jd":
        return await search_jd(keyword, page, page_size)
    if platform == "pdd":
        return await search_pdd(keyword, page, page_size)
    return []


async def search_all_platforms(keyword: str, page: int, page_size: int) -> List[Product]:
    tasks = [
        search_platform(keyword, page, page_size, "taobao"),
        search_platform(keyword, page, page_size, "jd"),
        search_platform(keyword, page, page_size, "pdd"),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged: List[Product] = []
    for platform_items in results:
        if isinstance(platform_items, Exception):
            continue
        merged.extend(platform_items)

    # 轻微打散，让展示更自然
    random.shuffle(merged)
    return merged[: page_size * 3]


async def search_marketplace(request: SearchRequest) -> SearchResponse:
    if request.keyword.strip():
        items = await search_all_platforms(request.keyword, request.page, request.page_size)
    else:
        items = []
    return SearchResponse(total=len(items), items=items)


async def debug_marketplace_request(platform: str, action: str, keyword: str | None = None, goods_id: str | None = None) -> dict:
    platform = platform.lower().strip()
    action = action.lower().strip()
    if platform == "taobao":
        return await debug_taobao_request(action=action, keyword=keyword, goods_id=goods_id)
    if platform == "jd":
        return await debug_jd_request(action=action, keyword=keyword, goods_id=goods_id)
    if platform == "pdd":
        return await debug_pdd_request(action=action, keyword=keyword, goods_id=goods_id)
    return {"ok": False, "error": f"不支持的平台：{platform}"}


async def get_marketplace_detail(platform: str, goods_id: str) -> dict:
    platform = platform.lower().strip()
    if platform == "taobao":
        return await get_taobao_detail(goods_id)
    if platform == "jd":
        return await get_jd_detail(goods_id)
    if platform == "pdd":
        return await get_pdd_detail(goods_id)
    return {"platform": platform, "goods_id": goods_id, "error": "unsupported platform"}


async def generate_marketplace_promotion_url(platform: str, goods_id: str) -> dict:
    platform = platform.lower().strip()
    if platform == "taobao":
        return await generate_taobao_promotion_url(goods_id, os.getenv("TAOBAO_PID", ""))
    if platform == "jd":
        return await generate_jd_promotion_url(goods_id)
    if platform == "pdd":
        return await generate_pdd_promotion_url(goods_id, os.getenv("PDD_PID", ""))
    return {"platform": platform, "goods_id": goods_id, "error": "unsupported platform"}


async def get_marketplace_orders(platform: str | None = None) -> dict:
    selected = [platform.lower().strip()] if platform else ["taobao", "jd", "pdd"]
    result = {}
    if "taobao" in selected:
        result["taobao"] = await get_taobao_orders()
    if "jd" in selected:
        result["jd"] = await get_jd_orders()
    if "pdd" in selected:
        result["pdd"] = await get_pdd_orders()
    return result


def platform_config_summary() -> dict:
    return {
        "taobao": {
            "configured": _has_platform_credentials("TAOBAO"),
            "pid_configured": bool(os.getenv("TAOBAO_PID")),
            "apis": {
                "search": get_platform_api_spec("taobao").search,
                "detail": get_platform_api_spec("taobao").detail,
                "promotion": get_platform_api_spec("taobao").promotion,
                "order": get_platform_api_spec("taobao").order,
            },
        },
        "jd": {
            "configured": _has_platform_credentials("JD"),
            "pid_configured": bool(os.getenv("JD_PID")),
            "apis": {
                "search": get_platform_api_spec("jd").search,
                "detail": get_platform_api_spec("jd").detail,
                "promotion": get_platform_api_spec("jd").promotion,
                "order": get_platform_api_spec("jd").order,
            },
        },
        "pdd": {
            "configured": _has_platform_credentials("PDD"),
            "pid_configured": bool(os.getenv("PDD_PID")),
            "apis": {
                "search": get_platform_api_spec("pdd").search,
                "detail": get_platform_api_spec("pdd").detail,
                "promotion": get_platform_api_spec("pdd").promotion,
                "order": get_platform_api_spec("pdd").order,
            },
        },
    }
