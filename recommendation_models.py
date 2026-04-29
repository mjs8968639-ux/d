"""
AI 购物推荐系统的数据模型。
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class UserRequest(BaseModel):
    """用户输入请求。"""

    query: str = Field(..., description="用户的一句话需求")
    mode: Optional[str] = Field(default=None, description="推荐模式：value、brand、cheap")


class ClickRequest(BaseModel):
    """点击统计请求。"""

    query: str = Field(..., description="搜索词")
    product_id: str = Field(..., description="商品 ID")
    product_title: Optional[str] = Field(default=None, description="商品标题")
    ranking_score: Optional[int] = Field(default=None, description="推荐排名分")
    impression_count: int = Field(default=1, description="本次点击对应的曝光数")


class UserIntent(BaseModel):
    """解析后的用户意图。"""

    raw_query: str
    product_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    scene: Optional[str] = None
    mode: Optional[str] = None
    features: List[str] = []
    extra_keywords: List[str] = []


class SearchKeywordPlan(BaseModel):
    """生成的搜索关键词方案。"""

    keywords: List[str]


class ProductCandidate(BaseModel):
    """电商返回的候选商品。"""

    id: str
    title: str
    price: float
    original_price: Optional[float] = None
    platform: str
    image_url: str
    sales: int = 0
    detail_url: str
    shop_name: Optional[str] = None
    tags: List[str] = []
    rating: Optional[float] = None


class RecommendedProduct(BaseModel):
    """最终推荐给前端展示的商品。"""

    title: str
    price: float
    platform: str
    reason: str
    score: int = 0
    ranking_score: int = 0
    ranking_reason: Optional[str] = None
    pros: List[str] = []
    cons: Optional[str] = None
    buy_link: str
    commission: Optional[float] = None


class RecommendationResponse(BaseModel):
    """推荐结果。"""

    query: str
    summary: str
    intent: UserIntent
    keywords: List[str]
    total_candidates: int
    recommendations: List[RecommendedProduct]
