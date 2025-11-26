"""
自定义 API 客户端
使用 requests 调用兼容 OpenAI 格式的 API
"""
import requests
from typing import Dict, Optional
from app.services.ai.base_client import BaseAIClient


class CustomAPIClient(BaseAIClient):
    """自定义 API 客户端（使用 requests，兼容 OpenAI 格式）"""
    
    def __init__(self, api_key: str, base_url: str,
                 model: str = "gpt-3.5-turbo", temperature: float = 0.7,
                 max_tokens: int = 500):
        """
        初始化自定义 API 客户端
        
        :param api_key: API 密钥
        :param base_url: 基础 URL（必需）
        :param model: 模型名称
        :param temperature: 温度参数
        :param max_tokens: 最大 token 数
        """
        if not base_url:
            raise ValueError("自定义 API 必须提供 base_url")
        
        super().__init__(api_key, base_url, model, temperature, max_tokens)
        
        # 确保 base_url 格式正确
        self.base_url = self.base_url.rstrip('/')
        if not self.base_url.endswith('/chat/completions'):
            self.base_url = self.base_url + '/chat/completions'
    
    def chat_completion(self, messages: list, **kwargs) -> Dict:
        """
        发送聊天补全请求（兼容 OpenAI 格式）
        
        :param messages: 消息列表
        :param kwargs: 其他参数
        :return: API 响应字典
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get('temperature', self.temperature),
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "response_format": {"type": "json_object"}  # 强制 JSON 格式
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 调用失败: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        :return: True 如果连接成功，False 否则
        """
        try:
            self.chat_completion([{"role": "user", "content": "test"}], max_tokens=5)
            return True
        except Exception:
            return False

