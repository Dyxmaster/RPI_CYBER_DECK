# config.py
import os

class Config:
    # 必须设置密钥，用于加密 Session
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'rpi-cyber-deck-secret-key-888'
    
    # 这里设置你的登录账号密码
    ADMIN_USER = "admin"
    ADMIN_PASS = "123456"  