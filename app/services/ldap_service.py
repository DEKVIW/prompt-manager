"""
LDAP认证服务
"""
from ldap3 import Server, Connection, ALL, SIMPLE
from flask import current_app
from app.database import get_db


def authenticate_ldap_user(email, password):
    """
    使用LDAP验证用户身份
    :param email: 用户邮箱
    :param password: 用户密码
    :return: (bool, dict) - 验证结果和用户信息
    """
    if not current_app.config['LDAP_ENABLED']:
        current_app.logger.debug("LDAP认证已禁用")
        return False, None
    
    try:
        current_app.logger.info(f"开始LDAP认证，输入: {email}")
        
        # 检查输入是邮箱还是uid
        is_email = '@' in email
        username = email.split('@')[0] if is_email else email
        current_app.logger.debug(f"提取用户名: {username}, 是邮箱: {is_email}")
        
        # 构建LDAP服务器连接
        server = Server(
            current_app.config['LDAP_SERVER'],
            port=current_app.config['LDAP_PORT'],
            get_info=ALL
        )
        current_app.logger.debug(f"连接LDAP服务器: {current_app.config['LDAP_SERVER']}:{current_app.config['LDAP_PORT']}")
        
        # 构建用户搜索过滤器
        # 支持根据uid或邮箱搜索用户
        if is_email:
            # 如果是邮箱，使用mail属性搜索
            user_search_filter = f"(&{current_app.config['LDAP_USER_SEARCH_FILTER']}(mail={email}))"
        else:
            # 如果是uid，使用uid属性搜索
            user_search_filter = f"(&{current_app.config['LDAP_USER_SEARCH_FILTER']}(uid={username}))"
        
        current_app.logger.debug(f"用户搜索过滤器: {user_search_filter}")
        
        # 使用绑定账号搜索用户
        with Connection(
            server,
            user=current_app.config['LDAP_BIND_DN'],
            password=current_app.config['LDAP_BIND_PASSWORD'],
            auto_bind=True
        ) as conn:
            current_app.logger.debug(f"成功绑定LDAP服务器，使用DN: {current_app.config['LDAP_BIND_DN']}")
            
            # 搜索用户
            current_app.logger.debug(f"搜索用户，基础DN: {current_app.config['LDAP_USER_SEARCH_BASE']}")
            conn.search(
                search_base=current_app.config['LDAP_USER_SEARCH_BASE'],
                search_filter=user_search_filter,
                attributes=['*']
            )
            
            current_app.logger.debug(f"搜索结果数量: {len(conn.entries)}")
            
            if len(conn.entries) == 0:
                current_app.logger.info(f"未找到LDAP用户: {username}")
                return False, None
            
            # 获取用户DN
            user_dn = conn.entries[0].entry_dn
            current_app.logger.debug(f"找到LDAP用户，DN: {user_dn}")
            
            # 使用用户凭证进行绑定验证
            with Connection(
                server,
                user=user_dn,
                password=password,
                authentication=SIMPLE,
                auto_bind=True
            ) as user_conn:
                current_app.logger.debug(f"LDAP用户绑定成功: {user_dn}")
                
                # 验证成功，获取用户信息
                user_attrs = conn.entries[0].entry_attributes_as_dict
                current_app.logger.debug(f"获取用户属性: {user_attrs}")
                
                # 映射LDAP属性到应用用户属性
                # 支持多个属性来源，按顺序查找
                username_attrs = ['uid', 'userid', 'sAMAccountName']
                email_attrs = ['mail', 'email', 'userPrincipalName']
                
                # 查找用户名
                found_username = username
                for attr in username_attrs:
                    if attr in user_attrs and user_attrs[attr]:
                        found_username = user_attrs[attr][0]
                        break
                
                # 查找邮箱
                found_email = email
                for attr in email_attrs:
                    if attr in user_attrs and user_attrs[attr]:
                        found_email = user_attrs[attr][0]
                        break
                
                user_info = {
                    'username': found_username,
                    'email': found_email
                }
                
                current_app.logger.info(f"LDAP认证成功，用户信息: {user_info}")
                return True, user_info
    except Exception as e:
        current_app.logger.error(f"LDAP认证失败: {str(e)}")
        return False, None


def create_or_update_ldap_user(user_info):
    """
    创建或更新LDAP用户到本地数据库
    :param user_info: LDAP用户信息
    :return: dict - 本地用户信息
    """
    db = get_db()
    
    # 检查用户是否已存在
    existing_user = db.execute(
        'SELECT * FROM users WHERE email = ?',
        (user_info['email'],)
    ).fetchone()
    
    if existing_user:
        # 用户已存在，更新信息
        db.execute(
            'UPDATE users SET username = ? WHERE email = ?',
            (user_info['username'], user_info['email'])
        )
        db.commit()
        return dict(existing_user)
    else:
        # 用户不存在，创建新用户
        # 生成随机密码，因为LDAP用户不需要本地密码
        from werkzeug.security import generate_password_hash
        random_password = generate_password_hash('ldap_user', method='pbkdf2:sha256')
        
        db.execute(
            '''
            INSERT INTO users (username, email, password_hash, is_approved)
            VALUES (?, ?, ?, ?)
            ''',
            (user_info['username'], user_info['email'], random_password, 0)
        )
        db.commit()
        
        # 获取新创建的用户
        new_user = db.execute(
            'SELECT * FROM users WHERE email = ?',
            (user_info['email'],)
        ).fetchone()
        
        return dict(new_user)
