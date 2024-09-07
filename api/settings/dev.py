from .base import *
from dotenv import load_dotenv

from .base import *
from dotenv import load_dotenv

dotenv_path = BASE_DIR / '.env.dev'
load_dotenv(dotenv_path)

SECRET_KEY = os.environ.get("SECRET_KEY")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")

class DevelopmentConfig(BaseConfig):

    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    SECRET_KEY = SECRET_KEY

    if 'test' in sys.argv or 'test_coverage' in sys.argv:  # Identifies when we're running tests
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
                'NAME': 'postgres',
                'USER': os.environ.get('SUPABASE_DB_USER'),
                'PASSWORD': os.environ.get('SUPABASE_DB_PASSWORD'),
                'HOST': os.environ.get('SUPABASE_DB_HOST'),
            }
        }

    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]
    CORS_TRUSTED_ORIGNS = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]

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

    CSRF_COOKIE_NAME = 'csrftoken'
    CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
    CSRF_USE_SESSIONS = False
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SAMESITE = 'Lax'
    CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000'] 


    SECRET_KEY = os.environ.get("SECRET_KEY")
    AUTH_USER_MODEL = 'authentication.FirebaseUser'

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        #Libs
        'rest_framework',
        'corsheaders',
        'firebase_admin',

        #Apps
        'apps.authentication.apps.AuthenticationConfig',
        'apps.brolympics.apps.BrolympicsConfig',
    ]

    MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',

        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    ROOT_URLCONF = 'api.urls'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    WSGI_APPLICATION = 'api.wsgi.application'

    AUTH_PASSWORD_VALIDATORS = [
        {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
        {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
        {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
        {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
    ]

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'apps.authentication.firebase.FirebaseAuthentication',
        ),
    }

    if 'test' in sys.argv or 'test_coverage' in sys.argv:  # Identifies when we're running tests
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
                'NAME': 'postgres',
                'USER': os.environ.get('SUPABASE_DB_USER'),
                'PASSWORD': os.environ.get('SUPABASE_DB_PASSWORD'),
                'HOST': os.environ.get('SUPABASE_DB_HOST'),
            }
        }


# Firebase initialization for development
FIREBASE_CREDENTIALS_PATH = BASE_DIR / '.serviceAccountKey.json'
if not firebase_admin._apps:
    cred = firebase_admin.credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

dev_settings = DevelopmentConfig()
dev_settings.FIREBASE_STORAGE_BUCKET = FIREBASE_STORAGE_BUCKET
dev_settings.FIREBASE_CREDENTIALS_PATH = FIREBASE_CREDENTIALS_PATH

# Make all attributes of BaseConfig available at the module level
for setting in dir(dev_settings):
    if setting.isupper():
        locals()[setting] = getattr(dev_settings, setting)


