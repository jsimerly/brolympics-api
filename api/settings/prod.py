from .base import *
from google.cloud import secretmanager
import json

DEBUG = False
ALLOWED_HOSTS = ['your-cloud-run-url.a.run.app']  # Update once we get a cloud run URL

def access_secret_version(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.environ.get('GOOGLE_CLOUD_PROJECT')}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

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
FIREBASE_STORAGE_BUCKET = access_secret_version("firebase_storage_bucket")
if not firebase_admin._apps:
    firebase_credentials = json.loads(access_secret_version("firebase_service_account"))
    cred = firebase_admin.credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)