"""
AI 购物推荐系统后端入口。
当前使用 mock 数据演示完整流程：
1. 解析用户需求
2. 生成搜索关键词
3. 模拟电商 API 获取列表
4. AI 筛选最优商品
5. 返回推荐结果与理由
"""
from __future__ import annotations

import os
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from recommendation_models import ClickRequest, UserRequest
from recommendation_pipeline import (
    build_recommendation_response,
    generate_search_keywords,
    fetch_products_by_keywords,
    parse_user_intent,
    _call_ai_select_products,
)

load_dotenv()

CLICK_STATS = {
    "product_clicks": defaultdict(int),
    "query_clicks": defaultdict(int),
    "query_impressions": defaultdict(int),
}
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CLICK_STATS_TTL_SECONDS = int(os.getenv("CLICK_STATS_TTL_SECONDS", "2592000"))
REDIS_CLIENT = None


app = FastAPI(
    title="AI 购物推荐系统",
    description="基于用户自然语言输入生成商品推荐，当前使用 mock 数据",
    version="1.0.0",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "message": "系统异常，请稍后重试",
            "data": None,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "message": str(exc.detail) if exc.detail else "网络错误",
            "data": None,
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def success_response(data, message: str = "ok") -> dict:
    return {"success": True, "message": message, "data": data}


def error_response(message: str = "网络错误", data=None) -> dict:
    return {"success": False, "message": message, "data": data}


def _get_redis_client():
    global REDIS_CLIENT
    if REDIS_CLIENT is not None:
        return REDIS_CLIENT
    try:
        import redis
        REDIS_CLIENT = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        REDIS_CLIENT.ping()
    except Exception:
        REDIS_CLIENT = False
    return REDIS_CLIENT if REDIS_CLIENT not in (None, False) else None


def _redis_hincrby(key: str, field: str, amount: int = 1) -> int:
    client = _get_redis_client()
    if not client:
        return 0
    pipe = client.pipeline()
    pipe.hincrby(key, field, amount)
    pipe.expire(key, CLICK_STATS_TTL_SECONDS)
    result = pipe.execute()
    return int(result[0]) if result else 0


def _redis_hgetall(key: str) -> dict:
    client = _get_redis_client()
    if not client:
        return {}
    try:
        return client.hgetall(key)
    except Exception:
        return {}


def _redis_keys_summary() -> dict:
    client = _get_redis_client()
    if not client:
        return {"redis_available": False}
    try:
        return {"redis_available": True, "redis_url": REDIS_URL}
    except Exception:
        return {"redis_available": False}


def build_debug_recommendation_payload(query: str) -> dict:
    intent = parse_user_intent(query)
    keyword_plan = generate_search_keywords(intent)
    candidates = fetch_products_by_keywords(keyword_plan.keywords)
    ai_raw = None

    try:
        ai_raw = _call_ai_select_products(candidates, intent, top_k=5)
    except Exception as exc:
        ai_raw = {"error": str(exc)}

    return {
        "query": query,
        "intent": intent.model_dump(),
        "keywords": keyword_plan.keywords,
        "candidate_count": len(candidates),
        "ai_raw": ai_raw,
    }


@app.get("/")
async def root() -> dict:
    return success_response(
        {
            "message": "AI 购物推荐系统运行中",
            "endpoints": {
                "recommend": "/recommend (POST)",
                "health": "/health (GET)",
                "debug_recommend": "/debug/recommend (POST)",
            },
        }
    )


@app.get("/health")
async def health() -> dict:
    return success_response({"status": "ok"})


@app.post("/recommend")
async def recommend(request: UserRequest) -> dict:
    """用户输入一句话，返回推荐结果。"""

    try:
        response = build_recommendation_response(request.query, top_k=5, mode=request.mode)
        _redis_hincrby("recommendation:query_impressions", request.query, len(response.recommendations))
        CLICK_STATS["query_impressions"][request.query] += len(response.recommendations)
        return success_response(response.model_dump())
    except HTTPException as exc:
        return error_response(message=str(exc.detail) if exc.detail else "网络错误")
    except Exception:
        try:
            fallback = build_recommendation_response(request.query, top_k=3, mode=request.mode)
            _redis_hincrby("recommendation:query_impressions", request.query, len(fallback.recommendations))
            CLICK_STATS["query_impressions"][request.query] += len(fallback.recommendations)
            return success_response(fallback.model_dump(), message="fallback")
        except Exception:
            return error_response(message="网络错误")


@app.post("/debug/recommend")
async def debug_recommend(request: UserRequest) -> dict:
    """返回调试信息和 AI 原始结果。"""

    try:
        payload = build_debug_recommendation_payload(request.query)
        return success_response(payload)
    except HTTPException as exc:
        return error_response(message=str(exc.detail) if exc.detail else "网络错误")
    except Exception:
        return error_response(message="网络错误")


@app.post("/click")
async def track_click(request: ClickRequest) -> dict:
    try:
        product_click_count = _redis_hincrby("recommendation:product_clicks", request.product_id, 1)
        query_click_count = _redis_hincrby("recommendation:query_clicks", request.query, 1)
        if request.impression_count > 0:
            _redis_hincrby("recommendation:query_impressions", request.query, request.impression_count)
        CLICK_STATS["product_clicks"][request.product_id] += 1
        CLICK_STATS["query_clicks"][request.query] += 1
        CLICK_STATS["query_impressions"][request.query] += max(request.impression_count, 0)
        return success_response(
            {
                "product_id": request.product_id,
                "query": request.query,
                "click_count": product_click_count or CLICK_STATS["product_clicks"][request.product_id],
                "query_click_count": query_click_count or CLICK_STATS["query_clicks"][request.query],
            },
            message="click recorded",
        )
    except Exception:
        return error_response(message="网络错误")


@app.get("/stats")
async def stats() -> dict:
    try:
        product_clicks = _redis_hgetall("recommendation:product_clicks")
        query_clicks = _redis_hgetall("recommendation:query_clicks")
        query_impressions = _redis_hgetall("recommendation:query_impressions")

        if not product_clicks and not query_clicks and not query_impressions:
            product_clicks = {k: str(v) for k, v in CLICK_STATS["product_clicks"].items()}
            query_clicks = {k: str(v) for k, v in CLICK_STATS["query_clicks"].items()}
            query_impressions = {k: str(v) for k, v in CLICK_STATS["query_impressions"].items()}

        def to_int_map(source: dict) -> dict:
            return {key: int(value) for key, value in source.items()}

        product_clicks_int = to_int_map(product_clicks)
        query_clicks_int = to_int_map(query_clicks)
        query_impressions_int = to_int_map(query_impressions)

        top_products = sorted(product_clicks_int.items(), key=lambda item: item[1], reverse=True)[:20]
        top_queries = sorted(query_clicks_int.items(), key=lambda item: item[1], reverse=True)[:20]
        top_ctr_queries = []
        for query, clicks in top_queries:
            impressions = max(query_impressions_int.get(query, 0), 0)
            ctr = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.0
            top_ctr_queries.append({"query": query, "clicks": clicks, "impressions": impressions, "ctr": ctr})

        query_ctr = {
            query: round((clicks / max(query_impressions_int.get(query, 0), 1)) * 100, 2)
            for query, clicks in query_clicks_int.items()
        }

        total_clicks = sum(product_clicks_int.values())
        total_impressions = sum(query_impressions_int.values())
        overall_ctr = round((total_clicks / max(total_impressions, 1)) * 100, 2)

        return success_response(
            {
                "redis": _redis_keys_summary(),
                "product_clicks": product_clicks_int,
                "query_clicks": query_clicks_int,
                "query_impressions": query_impressions_int,
                "query_ctr": query_ctr,
                "top_products": [{"product_id": pid, "clicks": count} for pid, count in top_products],
                "top_queries": [{"query": query, "clicks": count} for query, count in top_queries],
                "top_ctr_queries": top_ctr_queries,
                "overall_ctr": overall_ctr,
                "total_clicks": total_clicks,
                "total_impressions": total_impressions,
            }
        )
    except Exception:
        return error_response(message="网络错误")


if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
