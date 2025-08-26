"""
Configuration management for Flask VM Dashboard
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv('SESSION_TIMEOUT_HOURS', '12')))
    
    # Prism Central Configuration
    PRISM_IP = os.getenv('PRISM_IP')
    PRISM_USERNAME = os.getenv('PRISM_USERNAME')
    PRISM_PASSWORD = os.getenv('PRISM_PASSWORD')
    
    # Dashboard Authentication
    DASHBOARD_USERNAME = os.getenv('DASHBOARD_USERNAME')
    DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD')
    
    # Application Settings
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
    CLUSTER_CACHE_TTL = int(os.getenv('CLUSTER_CACHE_TTL', '300'))
    CONSOLE_BASE_URL = os.getenv('CONSOLE_BASE_URL', 'https://ntnxlab.ddns.net:8443')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            'SECRET_KEY', 'DASHBOARD_USERNAME', 'DASHBOARD_PASSWORD',
            'PRISM_IP', 'PRISM_USERNAME', 'PRISM_PASSWORD'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}