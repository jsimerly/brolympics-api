import os
import logging
from .base import *
from google.cloud import secretmanager
import json
import firebase_admin
from firebase_admin import credentials

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEBUG = False
ALLOWED_HOSTS = ['https://brolympics-api-708202517048.us-east5.run.app']  # Update once we get a cloud run URL

def access_secret_version(secret_id, version_id="latest"):
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        print(project_id)
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        logger.info(f"Attempting to access secret: {name}")
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {str(e)}")
        raise

try:
    SECRET_KEY = access_secret_version("django_secret_key")
    logger.info("Successfully retrieved SECRET_KEY")
except Exception as e:
    logger.error(f"Failed to retrieve SECRET_KEY: {str(e)}")
    raise

try:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': access_secret_version('db_name'),
            'USER': access_secret_version('db_user'),
            'PASSWORD': access_secret_version('db_password'),
            'HOST': access_secret_version('db_host'),
        }
    }
    logger.info("Successfully configured database settings")
except Exception as e:
    logger.error(f"Failed to configure database settings: {str(e)}")
    raise

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://brolympics-frontend-708202517048.us-east5.run.app",
    "https://brolympic.com", 
]

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
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Firebase initialization for production
try:
    FIREBASE_STORAGE_BUCKET = access_secret_version("firebase_storage_bucket")
    logger.info("Successfully retrieved FIREBASE_STORAGE_BUCKET")
    if not firebase_admin._apps:
        firebase_credentials = json.loads(access_secret_version("firebase_service_account"))
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {'storageBucket': FIREBASE_STORAGE_BUCKET})
        logger.info("Successfully initialized Firebase app")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {str(e)}")
    raise

logger.info("Production settings loaded successfully")