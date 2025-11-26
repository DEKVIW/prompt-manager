"""
OpenAI API 客户端
使用官方 OpenAI SDK
"""
from openai import OpenAI
from typing import Dict, Optional
from app.services.ai.base_client import BaseAIClient


class OpenAIClient(BaseAIClient):
    """OpenAI API 客户端（使用官方 SDK）"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None,
                 model: str = "gpt-3.5-turbo", temperature: float = 0.7,
                 max_tokens: int = 500):
        """
        初始化 OpenAI 客户端
        
        :param api_key: OpenAI API 密钥
        :param base_url: 自定义基础 URL（可选，用于代理或兼容 API）
        :param model: 模型名称
        :param temperature: 温度参数
        :param max_tokens: 最大 token 数
        """
        super().__init__(api_key, base_url, model, temperature, max_tokens)
        
        # 初始化 OpenAI 客户端
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = OpenAI(**client_kwargs)
    
    def chat_completion(self, messages: list, **kwargs) -> Dict:
        """
        发送聊天补全请求
        
        :param messages: 消息列表
        :param kwargs: 其他参数
        :return: API 响应字典
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                response_format={"type": "json_object"}  # 强制 JSON 格式
            )
            
            # 转换为统一的字典格式
            return {
                'choices': [{
                    'message': {
                        'content': response.choices[0].message.content
                    }
                }]
            }
        except Exception as e:
            raise Exception(f"OpenAI API 调用失败: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        :return: True 如果连接成功，False 否则
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
    
    def extract_text_from_response(self, response: Dict) -> str:
        """
        从响应中提取文本
        
        :param response: API 响应字典
        :return: 文本内容
        """
        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0].get('message', {}).get('content', '')
        return ''

