"""
京东平台搜索服务（模拟数据）
TODO: 后续接入京东联盟 API
"""
from typing import List
from models import Product
import random


async def search_jd(keyword: str, page: int, page_size: int) -> List[Product]:
    """
    搜索京东商品
    目前返回模拟数据，后续可替换为真实 API 调用
    """
    import asyncio
    await asyncio.sleep(0.3)
    
    base_id = (page - 1) * page_size
    products = []
    
    for i in range(page_size):
        price = round(random.uniform(60, 600), 2)
        original_price = round(price * random.uniform(1.15, 1.4), 2)
        sales = random.randint(200, 80000)
        
        products.append(Product(
            id=f"jd_{base_id + i}",
            title=f"【京东自营】{keyword} 京东配送 品质保证 {i+1}",
            price=price,
            original_price=original_price,
            platform="jd",
            image_url="https://via.placeholder.com/300x300?text=JD",
            sales=sales,
            detail_url=f"https://search.jd.com/Search?keyword={keyword}&page={page}",
            shop_name=f"京东自营旗舰店{i+1}",
            tags=["京东", "自营", "正品"]
        ))
    
    return products

