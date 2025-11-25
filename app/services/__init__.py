"""
业务逻辑层
"""
from app.services.tag_service import process_tags, link_tags_to_prompt
from app.services.prompt_service import (
    create_prompt, update_prompt, delete_prompt, get_prompt_by_id,
    get_user_prompts, get_public_prompts, is_favorited, toggle_favorite
)
from app.services.user_service import (
    authenticate_user, register_user, get_user_by_id, get_user_profile,
    update_user_profile, save_avatar, change_password
)
from app.services.admin_service import (
    generate_invite_code, generate_invite_codes, get_all_invite_codes,
    delete_invite_codes, get_all_users, ban_user, delete_user
)

__all__ = [
    # 标签服务
    'process_tags', 'link_tags_to_prompt',
    # 提示词服务
    'create_prompt', 'update_prompt', 'delete_prompt', 'get_prompt_by_id',
    'get_user_prompts', 'get_public_prompts', 'is_favorited', 'toggle_favorite',
    # 用户服务
    'authenticate_user', 'register_user', 'get_user_by_id', 'get_user_profile',
    'update_user_profile', 'save_avatar', 'change_password',
    # 管理员服务
    'generate_invite_code', 'generate_invite_codes', 'get_all_invite_codes',
    'delete_invite_codes', 'get_all_users', 'ban_user', 'delete_user'
]

