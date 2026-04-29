"""
拼多多平台搜索服务（模拟数据）
TODO: 后续接入拼多多联盟 API
"""
from typing import List
from models import Product
import random


async def search_pdd(keyword: str, page: int, page_size: int) -> List[Product]:
    """
    搜索拼多多商品
    目前返回模拟数据，后续可替换为真实 API 调用
    """
    import asyncio
    await asyncio.sleep(0.3)
    
    base_id = (page - 1) * page_size
    products = []
    
    for i in range(page_size):
        price = round(random.uniform(30, 300), 2)
        original_price = round(price * random.uniform(1.3, 1.8), 2)
        sales = random.randint(500, 100000)
        
        products.append(Product(
            id=f"pdd_{base_id + i}",
            title=f"【拼多多】{keyword} 限时特价 包邮到家 {i+1}",
            price=price,
            original_price=original_price,
            platform="pdd",
            image_url="https://via.placeholder.com/300x300?text=PDD",
            sales=sales,
            detail_url=f"https://mobile.yangkeduo.com/search_result.html?search_key={keyword}",
            shop_name=f"拼多多商家{i+1}",
            tags=["拼多多", "特价", "包邮"]
        ))
    
    return products

