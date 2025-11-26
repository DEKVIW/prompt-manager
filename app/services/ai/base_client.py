"""
AI 客户端抽象基类
定义统一的 AI API 调用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseAIClient(ABC):
    """AI 客户端抽象基类"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None,
                 model: str = "gpt-3.5-turbo", temperature: float = 0.7,
                 max_tokens: int = 500):
        """
        初始化 AI 客户端
        
        :param api_key: API 密钥
        :param base_url: 基础 URL（可选，用于自定义 API）
        :param model: 模型名称
        :param temperature: 温度参数（0.0-2.0）
        :param max_tokens: 最大 token 数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def chat_completion(self, messages: list, **kwargs) -> Dict:
        """
        发送聊天补全请求
        
        :param messages: 消息列表，格式：[{"role": "user", "content": "..."}]
        :param kwargs: 其他参数（temperature, max_tokens 等）
        :return: API 响应字典
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        :return: True 如果连接成功，False 否则
        """
        pass
    
    def extract_text_from_response(self, response: Dict) -> str:
        """
        从 API 响应中提取文本内容
        不同提供商的响应格式可能不同，子类可以重写此方法
        
        :param response: API 响应字典
        :return: 提取的文本内容
        """
        # 默认实现，子类可以覆盖
        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0].get('message', {}).get('content', '')
        return ''

