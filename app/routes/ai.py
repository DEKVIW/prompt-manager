"""
AI 相关路由
提供 AI 自动填充功能的 API 接口
"""
from flask import Blueprint, request, jsonify, session
from app.database import get_db
from app.utils.decorators import login_required
from app.utils.encryption import decrypt_string
from app.services.ai.factory import AIClientFactory
from app.services.ai_service import AIService
from flask import current_app

bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@bp.route('/generate-metadata', methods=['POST'])
@login_required
def generate_metadata():
    """
    生成提示词元数据
    
    请求体:
    {
        "content": "提示词内容",
        "title_max_length": 30,      // 可选，默认从用户配置读取
        "description_max_length": 100, // 可选，默认从用户配置读取
        "tag_count": 5,               // 可选，默认从用户配置读取
        "tag_two_char_count": 0,      // 可选，默认从用户配置读取
        "tag_four_char_count": 0      // 可选，默认从用户配置读取
    }
    
    返回:
    {
        "success": true,
        "title": "标题",
        "description": "描述",
        "tags": ["标签1", "标签2"]
    }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求体不能为空'}), 400
        
        content = data.get('content', '').strip()
        if not content:
            return jsonify({'success': False, 'message': '提示词内容不能为空'}), 400
        
        # 获取用户 AI 配置
        db = get_db()
        config = db.execute(
            'SELECT * FROM ai_configs WHERE user_id = ? AND enabled = 1',
            (user_id,)
        ).fetchone()
        
        if not config:
            return jsonify({
                'success': False,
                'message': '未配置 AI API，请先前往设置页面配置'
            }), 400
        
        # 将 Row 对象转换为字典
        config = dict(config)
        
        # 解密 API Key
        try:
            api_key = decrypt_string(config['api_key'])
        except Exception as e:
            current_app.logger.error(f'解密 API Key 失败: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'API Key 解密失败，请重新配置'
            }), 500
        
        # 创建 AI 客户端
        client = AIClientFactory.create_client(
            provider=config['provider'],
            api_key=api_key,
            base_url=config.get('base_url'),
            model=config.get('model', 'gpt-3.5-turbo'),
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 500)
        )
        
        # 创建 AI 服务
        ai_service = AIService(client)
        
        # 生成元数据（使用固定规则，不再接受参数）
        metadata = ai_service.generate_metadata(prompt_content=content)
        
        return jsonify({
            'success': True,
            'title': metadata['title'],
            'description': metadata['description'],
            'tags': metadata['tags']
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f'生成元数据失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'生成失败: {str(e)}'
        }), 500


@bp.route('/test-connection', methods=['POST'])
@login_required
def test_connection():
    """
    测试 AI API 连接
    
    请求体:
    {
        "provider": "openai",           // 可选，如果为空则使用已保存的配置
        "api_key": "sk-...",            // 可选，如果为空则使用已保存的 key
        "base_url": "https://...",      // 可选
        "model": "gpt-3.5-turbo"        // 可选
    }
    
    返回:
    {
        "success": true/false,
        "message": "连接成功" / "连接失败: 原因"
    }
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    try:
        data = request.get_json() or {}
        
        # 获取用户已保存的配置
        db = get_db()
        config = db.execute(
            'SELECT * FROM ai_configs WHERE user_id = ? AND enabled = 1',
            (user_id,)
        ).fetchone()
        
        # 如果输入框提供了新的 key，使用新的；否则使用已保存的
        api_key_input = data.get('api_key', '').strip()
        
        if api_key_input:
            # 使用输入框中的新 key
            api_key = api_key_input
            provider = data.get('provider', 'openai')
            base_url = data.get('base_url', '').strip() or None
            model = data.get('model', 'gpt-3.5-turbo')
        elif config:
            # 使用已保存的配置
            config = dict(config)
            try:
                api_key = decrypt_string(config['api_key'])
            except Exception as e:
                current_app.logger.error(f'解密 API Key 失败: {str(e)}')
                return jsonify({
                    'success': False,
                    'message': 'API Key 解密失败，请重新配置'
                }), 500
            
            provider = data.get('provider') or config.get('provider', 'openai')
            base_url = data.get('base_url', '').strip() or config.get('base_url')
            model = data.get('model') or config.get('model', 'gpt-3.5-turbo')
        else:
            # 既没有输入，也没有保存的配置
            return jsonify({
                'success': False,
                'message': '请先输入 API Key 或保存配置'
            }), 400
        
        if not api_key:
            return jsonify({'success': False, 'message': 'API Key 不能为空'}), 400
        
        # 创建 AI 客户端
        try:
            client = AIClientFactory.create_client(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                model=model,
                temperature=0.7,
                max_tokens=100
            )
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        
        # 测试连接
        if client.test_connection():
            return jsonify({
                'success': True,
                'message': '连接成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '连接失败，请检查 API Key 和配置'
            })
            
    except Exception as e:
        current_app.logger.error(f'测试连接失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500

