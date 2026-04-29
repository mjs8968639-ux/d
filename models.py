"""
数据模型定义
"""
from pydantic import BaseModel
from typing import List, Optional


class Product(BaseModel):
    id: str
    title: str
    price: float
    original_price: Optional[float] = None
    platform: str
    image_url: str
    sales: int = 0
    detail_url: str
    shop_name: Optional[str] = None
    tags: Optional[List[str]] = None
    rating: Optional[float] = None  # 新增：好评率
    reason: Optional[str] = None  # AI 推荐理由（MVP）


class SearchRequest(BaseModel):
    keyword: str
    page: int = 1
    page_size: int = 20
    sort: Optional[str] = "relevance"  # relevance, price_asc, price_desc, sales_desc, rating_desc
    category: Optional[str] = None  # 一级分类
    subcategory: Optional[str] = None  # 二级分类
    third_category: Optional[str] = None  # 三级分类（可选）


class SearchResponse(BaseModel):
    total: int
    items: List[Product]


class AISearchRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 20
    top_k: int = 5
    category: Optional[str] = None  # 多义词时可指定一级分类


class IntentInfo(BaseModel):
    product_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    scene: Optional[str] = None
    raw_query: str


class AISearchResponse(BaseModel):
    query: str
    intent: IntentInfo
    keywords: List[str]
    total_candidates: int
    items: List[Product]


class Category(BaseModel):  # 新增：分类模型
    name: str
    label: str
    icon: Optional[str] = None
    description: Optional[str] = None


class SubCategory(BaseModel):  # 新增：子分类模型
    name: str
    label: str
    count: Optional[int] = None


class ClassifyRequest(BaseModel):  # 新增：分类请求
    keyword: str


class ClassifyResponse(BaseModel):  # 新增：分类响应
    needs_classification: bool
    categories: List[Category] = []
    direct_search_keyword: Optional[str] = None  # 如果不需要分类，返回优化后的关键词


class SubClassifyRequest(BaseModel):  # 新增：子分类请求
    keyword: str
    category: Optional[str] = None  # 一级分类（多义关键词时需要）
    skip_level1: bool = False  # 是否跳过一级分类（单义大类关键词时）

class SubClassifyResponse(BaseModel):  # 新增：子分类响应
    subcategories: List[SubCategory]

class ThirdClassifyRequest(BaseModel):  # 三级分类请求
    keyword: str
    category: str  # 一级分类
    subcategory: str  # 二级分类

class ThirdClassifyResponse(BaseModel):  # 三级分类响应
    third_categories: List[SubCategory]


# 订单相关模型
class LogisticsStep(BaseModel):
    description: str
    time: str  # ISO 8601 格式时间字符串
    location: Optional[str] = None


class LogisticsInfo(BaseModel):
    tracking_number: Optional[str] = None
    logistics_company: Optional[str] = None
    steps: List[LogisticsStep] = []
    current_status: Optional[str] = None
    update_time: Optional[str] = None


class OrderProduct(BaseModel):
    id: str
    title: str
    price: float
    original_price: Optional[float] = None
    platform: str
    image_url: str
    sales: int = 0
    detail_url: str
    shop_name: Optional[str] = None
    tags: Optional[List[str]] = None


class Order(BaseModel):
    id: str
    products: List[OrderProduct]
    total_price: float
    status: str  # pending, paid, shipped, delivered, completed, cancelled
    create_time: str  # ISO 8601 格式时间字符串
    tracking_number: Optional[str] = None
    address: Optional[str] = None
    platform: str
    logistics_info: Optional[LogisticsInfo] = None


class OrderSyncRequest(BaseModel):
    taobao_token: Optional[str] = None
    jd_token: Optional[str] = None
    pdd_token: Optional[str] = None
    tmall_token: Optional[str] = None


class OrderSyncResponse(BaseModel):
    success: bool
    orders: List[Order] = []
    message: Optional[str] = None

