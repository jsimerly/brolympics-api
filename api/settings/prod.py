import os
import json
import logging
from firebase_admin import credentials
from urllib.parse import urlparse
from google.cloud import secretmanager

from .base import *

GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')
def access_secret_version(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    project_id = GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

ENV_TYPE = "PROD"
SECRET_KEY = access_secret_version("django_secret_key")
DEBUG = False

if "api" not in INSTALLED_APPS:
    INSTALLED_APPS.append("api")

ALLOWED_HOSTS = [    
    "brolympics-api-708202517048.us-east5.run.app",
]

CLOUDRUN_SERVICE_URL = access_secret_version("api-cloudrun-service-url")
if CLOUDRUN_SERVICE_URL:
    ALLOWED_HOSTS.append(urlparse(CLOUDRUN_SERVICE_URL).netloc)
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    raise ValueError("Must have cloudrun service url.")


if 'test' in sys.argv or 'test_coverage' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': access_secret_version('db_name'),
            'USER': access_secret_version('db_user'),
            'PASSWORD': access_secret_version('db_password'),
            'HOST': access_secret_version('db_host'),
        }
    }

#CORS settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://brolympics-api-s7dp3idmra-ul.a.run.app",
    "https://brolympics-api-708202517048.us-east5.run.app",
    "https://brolympics-frontend-708202517048.us-central1.run.app", #UPDATE
    "https://brolympics-frontend-s7dp3idmra-uc.a.run.app", #UPDATE
    "https://brolympic.com", 
]


CORS_ALLOW_CREDENTIALS = True
CORS_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

FIREBASE_STORAGE_BUCKET = access_secret_version("firebase_storage_bucket")
if not firebase_admin._apps:
    firebase_credentials = json.loads(access_secret_version("firebase_service_account"))
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {'storageBucket': FIREBASE_STORAGE_BUCKET})


print(CLOUDRUN_SERVICE_URL)
print(GOOGLE_CLOUD_PROJECT)
print(ALLOWED_HOSTS)
print(CORS_ALLOW_ALL_ORIGINS)