"""
物流定时同步服务 - 后台自动同步物流状态
"""
import asyncio
from datetime import datetime
from typing import Optional
from services.logistics_service import get_logistics_info, get_order_tracking
from services.db_service import DatabaseService
from models import LogisticsInfo


class LogisticsSyncService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.is_running = False
        self.sync_interval = 600  # 10分钟同步一次
    
    def _is_finished_status(self, status: Optional[str]) -> bool:
        """判断是否为终态（不再需要同步）"""
        if not status:
            return False
        finished_statuses = ["已签收", "已完成", "已送达", "异常", "已退回"]
        return any(fs in status for fs in finished_statuses)
    
    async def sync_single_order(
        self,
        order_id: str,
        platform: str,
        tracking_number: Optional[str] = None,
        company: Optional[str] = None
    ) -> bool:
        """同步单个订单的物流信息"""
        try:
            # 如果有物流单号，直接查询
            if tracking_number:
                logistics_info = await get_logistics_info(tracking_number, company)
            else:
                # 否则通过订单ID查询
                logistics_info = await get_order_tracking(order_id, platform)
            
            if not logistics_info:
                print(f"订单 {order_id} ({platform}) 未找到物流信息")
                return False
            
            # 判断是否已完成
            is_finished = self._is_finished_status(logistics_info.current_status)
            
            # 保存到数据库
            self.db_service.save_logistics_status(
                order_id=order_id,
                platform=platform,
                logistics_info=logistics_info,
                is_finished=is_finished
            )
            
            print(f"✓ 同步成功: {order_id} ({platform}) - {logistics_info.current_status}")
            return True
            
        except Exception as e:
            print(f"✗ 同步失败: {order_id} ({platform}) - {str(e)}")
            return False
    
    async def sync_all_unfinished_orders(self):
        """同步所有未完成的订单"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始同步物流信息...")
        
        unfinished_orders = self.db_service.get_unfinished_orders(limit=100)
        
        if not unfinished_orders:
            print("没有需要同步的订单")
            return
        
        print(f"找到 {len(unfinished_orders)} 个未完成订单，开始同步...")
        
        # 并发同步（最多10个并发）
        semaphore = asyncio.Semaphore(10)
        
        async def sync_with_limit(order_data):
            async with semaphore:
                order_id, platform, tracking_number, company = order_data
                await self.sync_single_order(
                    order_id=order_id,
                    platform=platform,
                    tracking_number=tracking_number,
                    company=company
                )
        
        tasks = [sync_with_limit(order_data) for order_data in unfinished_orders]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 同步完成\n")
    
    async def start_background_sync(self):
        """启动后台定时同步任务"""
        if self.is_running:
            print("同步服务已在运行")
            return
        
        self.is_running = True
        print(f"🚀 物流同步服务已启动，每 {self.sync_interval} 秒同步一次")
        
        while self.is_running:
            try:
                await self.sync_all_unfinished_orders()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                print(f"同步服务出错: {str(e)}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
    
    def stop_background_sync(self):
        """停止后台同步任务"""
        self.is_running = False
        print("物流同步服务已停止")
