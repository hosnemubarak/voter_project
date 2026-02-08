"""
Django settings for voter_project.
"""

from pathlib import Path
import os

# Load environment variables from .env file if it exists
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings - Override these in production
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-voter-project-secret-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# CSRF trusted origins - Load from environment variable
# Format: comma-separated list of origins (e.g., "http://127.0.0.1:*,http://localhost:*,https://yourdomain.com")
CSRF_TRUSTED_ORIGINS = [
    origin.strip() 
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:*,http://localhost:*').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Local apps
    'apps.core',
    'apps.voters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Allow Facebook in-app browser (WebView) to render the page
X_FRAME_OPTIONS = 'SAMEORIGIN'

ROOT_URLCONF = 'voter_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'voter_project.wsgi.application'

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# Supports SQLite (local), PostgreSQL (Docker), and MySQL (cPanel)
# Set DATABASE_URL or individual DB_* variables

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Parse DATABASE_URL for any database type
    import urllib.parse
    url = urllib.parse.urlparse(DATABASE_URL)
    
    # Determine engine from scheme
    if url.scheme == 'mysql':
        engine = 'django.db.backends.mysql'
        port = url.port or 3306
    elif url.scheme in ('postgres', 'postgresql'):
        engine = 'django.db.backends.postgresql'
        port = url.port or 5432
    else:
        engine = 'django.db.backends.sqlite3'
        port = None
    
    DATABASES = {
        'default': {
            'ENGINE': engine,
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': port,
        }
    }
elif os.environ.get('DB_ENGINE') == 'mysql':
    # MySQL configuration (cPanel/Production)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'voter_project'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
        }
    }
elif os.environ.get('DB_ENGINE') == 'postgresql':
    # PostgreSQL with individual variables
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'voter_project'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    # SQLite configuration (Local Development - Default)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise settings for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_ALLOW_ALL_ORIGINS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Application Settings
APP_NAME = os.environ.get('APP_NAME', "Voter Management System")

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    # Formatters define how log messages are displayed
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{asctime}] {levelname} {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
    },
    
    # Handlers determine where logs are sent
    'handlers': {
        # Console handler - for development
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        
        # File handler - general application logs
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        
        # Error file handler - errors and exceptions only
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'error.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        
        # Security file handler - authentication and security events
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    
    # Loggers define which logs go where
    'loggers': {
        # Django core loggers
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Application loggers
        'apps': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps.core': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
    
    # Root logger - catch-all for unconfigured loggers
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
