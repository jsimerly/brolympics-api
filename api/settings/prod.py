import os
import logging
from .base import *
from google.cloud import secretmanager
import json
import firebase_admin
from firebase_admin import credentials
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)

GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')
logging.info(f"GOOGLE_CLOUD_PROJECT: {GOOGLE_CLOUD_PROJECT}")
def access_secret_version(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    project_id = GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

CLOUDRUN_SERVICE_URL = "https://brolympics-api-s7dp3idmra-ul.a.run.app"
logging.info(f"CLOUDRUN_SERVICE_URL: {CLOUDRUN_SERVICE_URL}")

class ProductionConfig(BaseConfig):
    def __init__(self) -> None:
        super().__init__()

    ALLOWED_HOSTS = [
        "brolympics-api-708202517048.us-east5.run.app",
        "brolympic.com", 
    ]

    if CLOUDRUN_SERVICE_URL:
        ALLOWED_HOSTS.append(urlparse(CLOUDRUN_SERVICE_URL).netloc)
        CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
        SECURE_SSL_REDIRECT = True
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    else:
        raise ValueError("CLOUDRUN_SERVICE_URL must not be null.")

    SECRET_KEY = access_secret_version("django_secret_key")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': access_secret_version('db_name'),
            'USER': access_secret_version('db_user'),
            'PASSWORD': access_secret_version('db_password'),
            'HOST': access_secret_version('db_host'),
        }
    }

    # CORS settings
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        "https://brolympics-api-s7dp3idmra-ul.a.run.app",
        "https://brolympics-frontend-708202517048.us-east5.run.app",
        "https://brolympic.com", 
    ]
    CORS_ALLOW_CREDENTIALS = True
    CORS_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

    CORS_ALLOW_HEADERS = [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
    ]

# Firebase initialization for production
FIREBASE_STORAGE_BUCKET = access_secret_version("firebase_storage_bucket")
if not firebase_admin._apps:
    firebase_credentials = json.loads(access_secret_version("firebase_service_account"))
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {'storageBucket': FIREBASE_STORAGE_BUCKET})

prod_settings = ProductionConfig()
# Make all attributes of BaseConfig available at the module level
for setting in dir(prod_settings):
    if setting.isupper():
        locals()[setting] = getattr(prod_settings, setting)

