import os

class Config:
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    ZOHO_OAUTH_TOKEN = os.getenv('ZOHO_OAUTH_TOKEN')
    MONGO_USERNAME = os.getenv('MONGO_USERNAME')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
    MONGO_URL = os.getenv('MONGO_URL')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    POSTGRESQL_PARAM = {
        'dbname': os.getenv('POSTGRESQL_DBNAME'),
        'user': 'root',
        'password': os.getenv('POSTGRESQL_PASSWORD'),
        'host': os.getenv('POSTGRESQL_HOST'),
        'port': os.getenv('POSTGRESQL_PORT'),
    }
    SECRET_KEY = os.getenv(('SECRET_KEY'))