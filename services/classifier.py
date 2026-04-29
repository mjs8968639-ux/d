"""
分类服务（MVP 简化版）
仅保留多义关键词一级分类能力，其余分类逻辑全部停用。
"""
from typing import List, Dict, Optional, Tuple


# 多义关键词：保留核心能力（例如 苹果/小米 这种）
MULTI_MEANING_KEYWORDS: Dict[str, Dict] = {
    "苹果": {
        "categories": [
            {"name": "apple", "label": "Apple 数码产品", "icon": "🍎", "description": "iPhone、iPad、Mac 等"},
            {"name": "fruit", "label": "水果苹果", "icon": "🍎", "description": "新鲜苹果"},
        ]
    },
    "小米": {
        "categories": [
            {"name": "xiaomi", "label": "小米电子产品", "icon": "📱", "description": "手机、电视、智能设备"},
            {"name": "grain", "label": "小米谷物", "icon": "🌾", "description": "五谷杂粮"},
        ]
    },
    "华为": {
        "categories": [
            {"name": "huawei", "label": "华为产品", "icon": "📱", "description": "手机、平板、电脑"},
            {"name": "flower", "label": "华为花", "icon": "🌸", "description": "花卉植物"},
        ]
    },
}


def classify_keyword_type(keyword: str) -> Tuple[str, Optional[str]]:
    keyword_lower = keyword.lower().strip()
    if keyword_lower in MULTI_MEANING_KEYWORDS:
        return ("multi_meaning", None)
    return ("direct", None)


def needs_classification(keyword: str) -> bool:
    keyword_type, _ = classify_keyword_type(keyword)
    return keyword_type == "multi_meaning"


def needs_level2_classification(keyword: str, category: Optional[str] = None) -> bool:
    # MVP 阶段停用二级分类
    return False


def needs_level3_classification(keyword: str, category: str, subcategory: str) -> bool:
    # MVP 阶段停用三级分类
    return False


def get_categories(keyword: str) -> List[Dict]:
    keyword_lower = keyword.lower().strip()
    if keyword_lower in MULTI_MEANING_KEYWORDS:
        return MULTI_MEANING_KEYWORDS[keyword_lower]["categories"]
    return []


def get_level2_categories(keyword: str, category: Optional[str] = None) -> List[Dict]:
    # MVP 阶段停用二级分类
    return []


def get_level3_categories(keyword: str, category: str, subcategory: str) -> List[Dict]:
    # MVP 阶段停用三级分类
    return []


def optimize_search_keyword(
    keyword: str,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    third_category: Optional[str] = None,
) -> str:
    """
    仅做一级分类优化：
    - 命中多义关键词且用户选择了 category 时，使用对应 label 作为搜索词
    - 其余情况直接返回原关键词
    """
    if not category:
        return keyword

    categories = get_categories(keyword)
    for cat in categories:
        if cat["name"] == category:
            return cat["label"]
    return keyword
