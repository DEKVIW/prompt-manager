"""
AI 客户端工厂
根据配置创建对应的 AI 客户端实例
"""
from app.services.ai.base_client import BaseAIClient
from app.services.ai.openai_client import OpenAIClient
from app.services.ai.custom_client import CustomAPIClient


class AIClientFactory:
    """AI 客户端工厂"""
    
    @staticmethod
    def create_client(provider: str, api_key: str, base_url: str = None,
                     model: str = "gpt-3.5-turbo", temperature: float = 0.7,
                     max_tokens: int = 500) -> BaseAIClient:
        """
        根据提供商创建对应的客户端实例
        
        :param provider: 提供商名称（'openai', 'custom'）
        :param api_key: API 密钥
        :param base_url: 基础 URL（自定义 API 必需）
        :param model: 模型名称
        :param temperature: 温度参数
        :param max_tokens: 最大 token 数
        :return: AI 客户端实例
        :raises ValueError: 如果提供商不支持或参数无效
        """
        if provider == 'openai':
            return OpenAIClient(
                api_key=api_key,
                base_url=base_url,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif provider == 'custom':
            if not base_url:
                raise ValueError("自定义 API 必须提供 base_url")
            return CustomAPIClient(
                api_key=api_key,
                base_url=base_url,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")

