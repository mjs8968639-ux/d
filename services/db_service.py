"""
数据库服务 - 使用 SQLite 存储物流状态
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List
from models import LogisticsInfo, LogisticsStep


class DatabaseService:
    def __init__(self, db_path: str = "logistics.db"):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建物流状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logistics_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                tracking_number TEXT,
                logistics_company TEXT,
                current_status TEXT,
                steps_json TEXT,
                last_sync_time TEXT NOT NULL,
                last_change_time TEXT,
                is_finished BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(order_id, platform)
            )
        """)
        
        # 创建物流事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logistics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                event_time TEXT NOT NULL,
                is_notified BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logistics_order 
            ON logistics_status(order_id, platform)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logistics_finished 
            ON logistics_status(is_finished)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_order 
            ON logistics_events(order_id, platform)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_notified 
            ON logistics_events(is_notified)
        """)
        
        conn.commit()
        conn.close()
    
    def save_logistics_status(
        self,
        order_id: str,
        platform: str,
        logistics_info: LogisticsInfo,
        is_finished: bool = False
    ) -> bool:
        """保存或更新物流状态"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # 检查是否存在旧记录
        cursor.execute("""
            SELECT current_status, last_change_time 
            FROM logistics_status 
            WHERE order_id = ? AND platform = ?
        """, (order_id, platform))
        
        old_record = cursor.fetchone()
        old_status = old_record[0] if old_record else None
        
        # 序列化步骤
        steps_json = json.dumps([
            {
                "description": step.description,
                "time": step.time,
                "location": step.location
            }
            for step in logistics_info.steps
        ])
        
        # 判断状态是否变化
        status_changed = old_status != logistics_info.current_status
        last_change_time = now if status_changed else (old_record[1] if old_record else now)
        
        # 插入或更新
        cursor.execute("""
            INSERT INTO logistics_status (
                order_id, platform, tracking_number, logistics_company,
                current_status, steps_json, last_sync_time, last_change_time,
                is_finished, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(order_id, platform) DO UPDATE SET
                tracking_number = excluded.tracking_number,
                logistics_company = excluded.logistics_company,
                current_status = excluded.current_status,
                steps_json = excluded.steps_json,
                last_sync_time = excluded.last_sync_time,
                last_change_time = excluded.last_change_time,
                is_finished = excluded.is_finished,
                updated_at = excluded.updated_at
        """, (
            order_id, platform,
            logistics_info.tracking_number,
            logistics_info.logistics_company,
            logistics_info.current_status,
            steps_json,
            now,
            last_change_time,
            1 if is_finished else 0,
            now,
            now
        ))
        
        # 如果状态变化，记录事件
        if status_changed and old_status is not None:
            cursor.execute("""
                INSERT INTO logistics_events (
                    order_id, platform, old_status, new_status,
                    event_time, is_notified, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id, platform, old_status,
                logistics_info.current_status, now, 0, now
            ))
        
        conn.commit()
        conn.close()
        return True
    
    def get_logistics_status(
        self,
        order_id: str,
        platform: str
    ) -> Optional[LogisticsInfo]:
        """从数据库获取物流状态"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tracking_number, logistics_company, current_status,
                   steps_json, last_sync_time, last_change_time
            FROM logistics_status
            WHERE order_id = ? AND platform = ?
        """, (order_id, platform))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # 反序列化步骤
        steps_data = json.loads(row[3]) if row[3] else []
        steps = [
            LogisticsStep(
                description=step["description"],
                time=step["time"],
                location=step.get("location")
            )
            for step in steps_data
        ]
        
        return LogisticsInfo(
            tracking_number=row[0],
            logistics_company=row[1],
            current_status=row[2],
            steps=steps,
            update_time=row[4]
        )
    
    def get_unfinished_orders(self, limit: int = 100) -> List[tuple]:
        """获取所有未完成的订单（用于定时同步）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT order_id, platform, tracking_number, logistics_company
            FROM logistics_status
            WHERE is_finished = 0
            ORDER BY last_sync_time ASC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [(row[0], row[1], row[2], row[3]) for row in results]
    
    def get_unnotified_events(self, limit: int = 100) -> List[dict]:
        """获取未通知的物流事件"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, order_id, platform, old_status, new_status, event_time
            FROM logistics_events
            WHERE is_notified = 0
            ORDER BY event_time DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "order_id": row[1],
                "platform": row[2],
                "old_status": row[3],
                "new_status": row[4],
                "event_time": row[5]
            }
            for row in results
        ]
    
    def mark_event_notified(self, event_id: int):
        """标记事件已通知"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE logistics_events
            SET is_notified = 1
            WHERE id = ?
        """, (event_id,))
        
        conn.commit()
        conn.close()
