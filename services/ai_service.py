"""
AI 搜索服务（MVP）
目标：query -> intent -> keywords -> filter + reason
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from models import Product


@dataclass
class Intent:
    raw_query: str
    product_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    scene: Optional[str] = None


PRODUCT_TYPE_HINTS = [
    "耳机",
    "键盘",
    "鼠标",
    "手机",
    "平板",
    "笔记本",
    "电脑",
    "路由器",
]

SCENE_HINTS = [
    "打游戏",
    "游戏",
    "通勤",
    "办公",
    "学习",
    "出差",
    "跑步",
    "睡眠",
]


def _parse_budget(query: str) -> tuple[Optional[float], Optional[float]]:
    budget_max = None
    budget_min = None

    m = re.search(r"预算\s*(\d+)", query)
    if m:
        budget_max = float(m.group(1))

    m = re.search(r"(\d+)\s*[-到~]\s*(\d+)", query)
    if m:
        budget_min = float(m.group(1))
        budget_max = float(m.group(2))
        if budget_min > budget_max:
            budget_min, budget_max = budget_max, budget_min

    m = re.search(r"(\d+)\s*以内", query)
    if m:
        budget_max = float(m.group(1))

    m = re.search(r"(\d+)\s*以上", query)
    if m:
        budget_min = float(m.group(1))

    return budget_min, budget_max


def parse_user_intent(query: str) -> Intent:
    normalized = query.strip()
    budget_min, budget_max = _parse_budget(normalized)

    product_type = next((x for x in PRODUCT_TYPE_HINTS if x in normalized), None)
    scene = next((x for x in SCENE_HINTS if x in normalized), None)

    return Intent(
        raw_query=normalized,
        product_type=product_type,
        budget_min=budget_min,
        budget_max=budget_max,
        scene=scene,
    )


def generate_keywords(intent: Intent) -> List[str]:
    keywords: List[str] = []

    if intent.product_type and intent.scene:
        keywords.append(f"{intent.scene}{intent.product_type}")
    if intent.product_type:
        keywords.append(intent.product_type)
    if intent.scene:
        keywords.append(intent.scene)

    if not keywords:
        keywords.append(intent.raw_query)
    else:
        keywords.append(intent.raw_query)

    # 去重并保持顺序
    unique_keywords: List[str] = []
    seen = set()
    for kw in keywords:
        item = kw.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        unique_keywords.append(item)
    return unique_keywords


def _score_product(product: Product, intent: Intent) -> float:
    score = 0.0
    title = product.title or ""

    if intent.product_type and intent.product_type in title:
        score += 3.0
    if intent.scene and intent.scene in title:
        score += 2.0

    # 销量轻加权，防止过度主导
    score += min(product.sales / 50000.0, 1.0)

    if intent.budget_max is not None:
        if product.price <= intent.budget_max:
            score += 2.0
        else:
            # 超预算按比例扣分
            over_ratio = (product.price - intent.budget_max) / max(intent.budget_max, 1.0)
            score -= min(over_ratio * 4.0, 4.0)

    if intent.budget_min is not None and product.price >= intent.budget_min:
        score += 0.5

    return score


def _build_reason(product: Product, intent: Intent) -> str:
    reasons: List[str] = []

    if intent.budget_max is not None:
        if product.price <= intent.budget_max:
            reasons.append(f"价格在预算 {int(intent.budget_max)} 元内")
        else:
            reasons.append(f"价格略高于预算 {int(intent.budget_max)} 元")

    if intent.scene:
        reasons.append(f"标题与“{intent.scene}”场景相关")

    if product.sales > 0:
        reasons.append(f"销量约 {product.sales}")

    if not reasons:
        reasons.append("与搜索意图匹配度较高")

    return "，".join(reasons[:3])


def filter_products(products: List[Product], intent: Intent, top_k: int = 5) -> List[Product]:
    scored = sorted(products, key=lambda p: _score_product(p, intent), reverse=True)

    selected: List[Product] = []
    for item in scored[: max(top_k, 1)]:
        cloned = item.copy(deep=True)
        cloned.reason = _build_reason(item, intent)
        selected.append(cloned)

    return selected
