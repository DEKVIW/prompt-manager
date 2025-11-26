"""
加密工具模块
用于加密和解密敏感数据（如 API Key）
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class Encryption:
    """加密工具类"""
    
    _key = None
    
    @classmethod
    def get_key(cls) -> bytes:
        """
        获取加密密钥
        优先从环境变量获取，否则使用默认密钥（仅用于开发环境）
        """
        if cls._key is not None:
            return cls._key
        
        # 尝试从环境变量获取密钥
        env_key = os.environ.get('AI_ENCRYPTION_KEY')
        
        if env_key:
            try:
                # 如果环境变量是 base64 编码的，直接使用
                cls._key = base64.urlsafe_b64decode(env_key.encode())
                return cls._key
            except Exception:
                # 如果不是 base64，使用 PBKDF2 派生密钥
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'prompt_manager_salt',  # 固定盐值（生产环境应使用随机盐）
                    iterations=100000,
                    backend=default_backend()
                )
                cls._key = base64.urlsafe_b64encode(kdf.derive(env_key.encode()))
                return cls._key
        
        # 开发环境默认密钥（生产环境必须设置环境变量）
        default_key = b'dev_key_for_prompt_manager_encryption_12345678'
        cls._key = base64.urlsafe_b64encode(default_key[:32])
        return cls._key
    
    @classmethod
    def generate_key(cls) -> str:
        """
        生成新的加密密钥（base64 编码）
        用于生产环境配置
        """
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        加密字符串
        
        :param plaintext: 明文
        :return: 加密后的 base64 编码字符串
        """
        if not plaintext:
            return ''
        
        key = cls.get_key()
        f = Fernet(key)
        encrypted = f.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        解密字符串
        
        :param ciphertext: 加密的 base64 编码字符串
        :return: 解密后的明文
        """
        if not ciphertext:
            return ''
        
        try:
            key = cls.get_key()
            f = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = f.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            # 如果解密失败，可能是旧格式或损坏的数据
            raise ValueError(f"解密失败: {str(e)}")


# 便捷函数
def encrypt_string(plaintext: str) -> str:
    """加密字符串的便捷函数"""
    return Encryption.encrypt(plaintext)


def decrypt_string(ciphertext: str) -> str:
    """解密字符串的便捷函数"""
    return Encryption.decrypt(ciphertext)

