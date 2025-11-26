"""
AI 服务层
提供统一的 AI 元数据生成接口
"""
import json
import re
from typing import Dict
from flask import current_app
from app.services.ai.base_client import BaseAIClient


# 提示词模板（固定规则）
METADATA_GENERATION_PROMPT = """你是一个专业的提示词管理助手。请根据用户提供的提示词内容，生成以下信息：

1. **标题**：一个简洁、准确的标题，能够概括提示词的核心功能或用途
   - 要求：不超过30个字符，使用中文
   - 风格：专业、简洁、易于理解

2. **描述**：一段简要的描述，说明这个提示词的用途、适用场景和特点
   - 要求：必须100-150个字符之间，使用中文
   - 内容：详细说明用途、适用场景、主要特点，确保描述充分且完整
   - 重要：描述字数必须严格控制在100-150字符之间，不能少于100字符，不能超过150字符

3. **标签**：生成5个相关标签，用于分类和搜索
   - 要求：标签使用中文或英文（技术术语）
   - 类型：技术标签、功能标签、场景标签
   - 每个标签长度2-8个字符

**输出格式**：必须严格按照以下 JSON 格式返回，不要包含任何其他文字说明：

```json
{{
    "title": "标题内容",
    "description": "描述内容",
    "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"]
}}
```

**用户提供的提示词内容**：
{prompt_content}

请开始分析并生成元数据："""


class AIService:
    """AI 服务类"""
    
    def __init__(self, client: BaseAIClient):
        """
        初始化 AI 服务
        
        :param client: AI 客户端实例
        """
        self.client = client
    
    def generate_metadata(self, prompt_content: str) -> Dict:
        """
        根据提示词内容生成元数据
        
        :param prompt_content: 提示词内容
        :return: 包含 title, description, tags 的字典
        :raises ValueError: 如果输入无效或生成失败
        """
        # 固定配置
        title_max_length = 30
        description_max_length = 150  # 最大150字符
        description_min_length = 100  # 最小100字符
        tag_count = 5
        tag_two_char_count = 0
        tag_four_char_count = 0
        # 验证输入
        if not prompt_content or len(prompt_content.strip()) == 0:
            raise ValueError("提示词内容不能为空")
        
        if len(prompt_content) > 10000:
            raise ValueError("提示词内容过长（最大10000字符）")
        
        # 构建提示词（使用固定规则）
        full_prompt = self._build_prompt(prompt_content=prompt_content)
        
        # 计算合适的 max_tokens
        # 标题大约需要 50 tokens，描述需要更多（150字符约300 tokens），标签每个约 10 tokens
        # 加上 JSON 格式的开销，总需求约为：50 + 300 + tag_count * 10 + 100
        estimated_tokens = 50 + 300 + (tag_count * 10) + 100
        # 确保至少 500，最多不超过 2000
        max_tokens = max(500, min(estimated_tokens, 2000))
        
        # 调用 AI API
        messages = [
            {"role": "system", "content": "你是一个专业的提示词管理助手，擅长分析提示词内容并生成准确的元数据。"},
            {"role": "user", "content": full_prompt}
        ]
        
        try:
            response = self.client.chat_completion(messages, max_tokens=max_tokens)
            content = self.client.extract_text_from_response(response)
            
            # 解析 JSON 响应
            metadata = self._parse_response(content)
            
            # 验证和清理数据（使用固定参数）
            metadata = self._validate_and_clean_metadata(
                metadata,
                title_max_length=title_max_length,
                description_min_length=description_min_length,
                description_max_length=description_max_length,
                tag_count=tag_count,
                tag_two_char_count=tag_two_char_count,
                tag_four_char_count=tag_four_char_count
            )
            
            return metadata
            
        except json.JSONDecodeError as e:
            raise ValueError(f"AI 返回的 JSON 格式错误: {str(e)}")
        except Exception as e:
            raise Exception(f"生成元数据失败: {str(e)}")
    
    def _build_prompt(self, prompt_content: str) -> str:
        """
        构建提示词（使用固定规则）
        
        :param prompt_content: 提示词内容
        :return: 完整的提示词
        """
        return METADATA_GENERATION_PROMPT.format(
            prompt_content=prompt_content
        )
    
    def _parse_response(self, content: str) -> Dict:
        """
        解析 AI 返回的内容
        
        :param content: AI 返回的文本内容
        :return: 解析后的字典
        :raises ValueError: 如果无法解析 JSON
        """
        # 尝试直接解析 JSON
        try:
            # 移除可能的代码块标记
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            content = content.strip()
            
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取 JSON 部分
            json_match = re.search(r'\{[^{}]*"title"[^{}]*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("无法从响应中提取有效的 JSON 数据")
    
    def _validate_and_clean_metadata(self, metadata: Dict,
                                    title_max_length: int = 30,
                                    description_min_length: int = 100,
                                    description_max_length: int = 150,
                                    tag_count: int = 5,
                                    tag_two_char_count: int = 0,
                                    tag_four_char_count: int = 0) -> Dict:
        """
        验证和清理元数据
        
        :param metadata: AI 返回的元数据
        :param title_max_length: 标题最大字数
        :param description_max_length: 描述最大字数
        :param tag_count: 标签总数
        :param tag_two_char_count: 两字标签个数
        :param tag_four_char_count: 四字标签个数
        :return: 清理后的元数据
        :raises ValueError: 如果数据无效
        """
        # 验证必需字段
        if 'title' not in metadata or 'description' not in metadata or 'tags' not in metadata:
            raise ValueError("AI 返回的数据缺少必需字段")
        
        # 清理标题（使用配置的长度限制）
        title = str(metadata['title']).strip()
        if len(title) > title_max_length:
            title = title[:title_max_length]
        if not title:
            raise ValueError("标题不能为空")
        
        # 清理描述（使用固定的长度限制：100-150字符）
        description = str(metadata['description']).strip()
        if len(description) > description_max_length:
            description = description[:description_max_length]
        elif len(description) < description_min_length:
            # 如果描述太短，提示但不强制（因为可能是 AI 生成的问题）
            current_app.logger.warning(f"描述字数不足：{len(description)} < {description_min_length}")
        if not description:
            raise ValueError("描述不能为空")
        
        # 清理标签（根据配置规则）
        tags = metadata.get('tags', [])
        if not isinstance(tags, list):
            tags = [tags] if tags else []
        
        # 过滤和清理标签
        cleaned_tags = []
        two_char_tags = []
        four_char_tags = []
        other_tags = []
        
        for tag in tags:
            tag = str(tag).strip()
            if not tag or len(tag) < 2 or len(tag) > 20:
                continue
            
            if len(tag) == 2:
                two_char_tags.append(tag)
            elif len(tag) == 4:
                four_char_tags.append(tag)
            else:
                other_tags.append(tag)
        
        # 按照配置规则选择标签
        if tag_two_char_count > 0:
            cleaned_tags.extend(two_char_tags[:tag_two_char_count])
        if tag_four_char_count > 0:
            cleaned_tags.extend(four_char_tags[:tag_four_char_count])
        
        # 填充剩余标签
        remaining = tag_count - len(cleaned_tags)
        if remaining > 0:
            all_remaining = two_char_tags[tag_two_char_count:] + \
                          four_char_tags[tag_four_char_count:] + \
                          other_tags
            cleaned_tags.extend(all_remaining[:remaining])
        
        # 确保标签数量在合理范围内
        if len(cleaned_tags) < 1:
            raise ValueError("至少需要一个标签")
        if len(cleaned_tags) > tag_count:
            cleaned_tags = cleaned_tags[:tag_count]
        
        return {
            'title': title,
            'description': description,
            'tags': cleaned_tags
        }
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        :return: True 如果连接成功，False 否则
        """
        return self.client.test_connection()

