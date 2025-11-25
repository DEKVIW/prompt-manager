"""
辅助函数
"""
import datetime


def format_datetime(dt):
    """将日期时间格式化为只显示年月日"""
    if isinstance(dt, datetime.datetime) or (isinstance(dt, str) and dt):
        try:
            if isinstance(dt, str):
                dt = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            return dt
    return '未知时间'

