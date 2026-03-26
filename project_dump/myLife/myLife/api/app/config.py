import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///mylife.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

def get_config():
    return Config
