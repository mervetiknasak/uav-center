import os
from pathlib import Path

from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured

from .env import env_bool, env_choice, env_int, env_list, load_env_file
from .network import InvalidServiceUrl, validated_browser_origin, validated_http_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_env_file(BASE_DIR / ".env")

APP_ENV = env_choice(
    "APP_ENV",
    choices={"development", "test", "production"},
    default="development",
)
IS_PRODUCTION = APP_ENV == "production"

DEVELOPMENT_SECRET_KEY = "dev-only-change-me"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", DEVELOPMENT_SECRET_KEY)
DEBUG = env_bool("DJANGO_DEBUG", not IS_PRODUCTION)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    [] if IS_PRODUCTION else ["localhost", "127.0.0.1", "testserver"],
)

if IS_PRODUCTION:
    if SECRET_KEY == DEVELOPMENT_SECRET_KEY or len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5:
        raise ImproperlyConfigured(
            "Production için DJANGO_SECRET_KEY en az 50 karakterli, benzersiz ve rastgele olmalıdır."
        )
    if DEBUG:
        raise ImproperlyConfigured("Production ortamında DJANGO_DEBUG=false olmalıdır.")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("Production için DJANGO_ALLOWED_HOSTS açıkça tanımlanmalıdır.")
    if any("*" in host or host.startswith(".") for host in ALLOWED_HOSTS):
        raise ImproperlyConfigured(
            "Production ortamında DJANGO_ALLOWED_HOSTS wildcard değer içeremez."
        )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("DATABASE_NAME", str(BASE_DIR / "db.sqlite3")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "tr-tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DOCUMENT_MAX_UPLOAD_SIZE = env_int("DOCUMENT_MAX_UPLOAD_SIZE", 25 * 1024 * 1024)
DATA_UPLOAD_MAX_MEMORY_SIZE = env_int(
    "DATA_UPLOAD_MAX_MEMORY_SIZE",
    DOCUMENT_MAX_UPLOAD_SIZE + 2 * 1024 * 1024,
)
FILE_UPLOAD_MAX_MEMORY_SIZE = env_int("FILE_UPLOAD_MAX_MEMORY_SIZE", 25 * 1024 * 1024)

DOCUMENT_MAX_TEXT_LENGTH = env_int("DOCUMENT_MAX_TEXT_LENGTH", 120_000)
DOCUMENT_MAX_ARCHIVE_ENTRIES = env_int("DOCUMENT_MAX_ARCHIVE_ENTRIES", 2_000)
DOCUMENT_MAX_UNCOMPRESSED_SIZE = env_int(
    "DOCUMENT_MAX_UNCOMPRESSED_SIZE",
    100 * 1024 * 1024,
)
DOCUMENT_MAX_PDF_PAGES = env_int("DOCUMENT_MAX_PDF_PAGES", 500)
RAG_CHUNK_SIZE = env_int("RAG_CHUNK_SIZE", 1400)
RAG_CHUNK_OVERLAP = env_int("RAG_CHUNK_OVERLAP", 220)
RAG_TOP_K = env_int("RAG_TOP_K", 6)
OCR_MODEL_DIR = os.getenv("OCR_MODEL_DIR", str(BASE_DIR / "ocr_models"))
OCR_ALLOW_MODEL_DOWNLOAD = env_bool("OCR_ALLOW_MODEL_DOWNLOAD", False)
OCR_USE_GPU = env_bool("OCR_USE_GPU", False)
OCR_MAX_IMAGES = env_int("OCR_MAX_IMAGES", 50)
OCR_MAX_PIXELS = env_int("OCR_MAX_PIXELS", 20_000_000)
OCR_PDF_DPI = env_int("OCR_PDF_DPI", 200)
OCR_PDF_MIN_TEXT_LENGTH = env_int("OCR_PDF_MIN_TEXT_LENGTH", 40)

POSITIVE_RESOURCE_LIMITS = {
    "DOCUMENT_MAX_UPLOAD_SIZE": DOCUMENT_MAX_UPLOAD_SIZE,
    "DOCUMENT_MAX_TEXT_LENGTH": DOCUMENT_MAX_TEXT_LENGTH,
    "DOCUMENT_MAX_ARCHIVE_ENTRIES": DOCUMENT_MAX_ARCHIVE_ENTRIES,
    "DOCUMENT_MAX_UNCOMPRESSED_SIZE": DOCUMENT_MAX_UNCOMPRESSED_SIZE,
    "DOCUMENT_MAX_PDF_PAGES": DOCUMENT_MAX_PDF_PAGES,
    "OCR_MAX_IMAGES": OCR_MAX_IMAGES,
    "OCR_MAX_PIXELS": OCR_MAX_PIXELS,
}
invalid_resource_limits = [name for name, value in POSITIVE_RESOURCE_LIMITS.items() if value <= 0]
if invalid_resource_limits:
    raise ImproperlyConfigured(
        "Belge kaynak sınırları pozitif olmalıdır: " + ", ".join(invalid_resource_limits)
    )

JOB_MAX_ATTEMPTS = env_int("JOB_MAX_ATTEMPTS", 3)
JOB_RETRY_BASE_SECONDS = env_int("JOB_RETRY_BASE_SECONDS", 15)
JOB_STALE_TIMEOUT = env_int("JOB_STALE_TIMEOUT", 7200)
AI_PROVIDER = env_choice(
    "AI_PROVIDER",
    choices={"local", "ollama", "local_llm", "local-http", "local_http"},
    default="local",
)
AI_ALLOW_REMOTE_SERVICES = env_bool("AI_ALLOW_REMOTE_SERVICES", False)
try:
    OLLAMA_BASE_URL = validated_http_url(
        os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        setting_name="OLLAMA_BASE_URL",
        require_local=not AI_ALLOW_REMOTE_SERVICES,
        require_https_for_remote=IS_PRODUCTION,
    )
except InvalidServiceUrl as exc:
    raise ImproperlyConfigured(str(exc)) from exc
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_TIMEOUT = env_int("OLLAMA_TIMEOUT", 600)
OLLAMA_PULL_TIMEOUT = env_int("OLLAMA_PULL_TIMEOUT", 3600)
LOCAL_LLM_TIMEOUT = env_int("LOCAL_LLM_TIMEOUT", 180)
try:
    LOCAL_LLM_BASE_URL = validated_http_url(
        os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8001"),
        setting_name="LOCAL_LLM_BASE_URL",
        require_local=not AI_ALLOW_REMOTE_SERVICES,
        require_https_for_remote=IS_PRODUCTION,
    )
except InvalidServiceUrl as exc:
    raise ImproperlyConfigured(str(exc)) from exc
LOCAL_LLM_API_KEY = os.getenv("LOCAL_LLM_API_KEY", "")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", os.getenv("QWEN_MODEL", "qwen2.5:14b"))
QWEN_MODEL = LOCAL_LLM_MODEL  # Backwards-compatible alias for existing deployments.
WHISPER_CONNECTION = env_choice(
    "WHISPER_CONNECTION",
    choices={"local", "http", "local_http", "local-http"},
    default="local",
)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_TIMEOUT = env_int("WHISPER_TIMEOUT", 180)
try:
    WHISPER_BASE_URL = validated_http_url(
        os.getenv("WHISPER_BASE_URL", "http://127.0.0.1:8002"),
        setting_name="WHISPER_BASE_URL",
        require_local=not AI_ALLOW_REMOTE_SERVICES,
        require_https_for_remote=IS_PRODUCTION,
    )
except InvalidServiceUrl as exc:
    raise ImproperlyConfigured(str(exc)) from exc

SERVICE_TIMEOUTS = {
    "OLLAMA_TIMEOUT": OLLAMA_TIMEOUT,
    "OLLAMA_PULL_TIMEOUT": OLLAMA_PULL_TIMEOUT,
    "LOCAL_LLM_TIMEOUT": LOCAL_LLM_TIMEOUT,
    "WHISPER_TIMEOUT": WHISPER_TIMEOUT,
}
invalid_service_timeouts = [name for name, value in SERVICE_TIMEOUTS.items() if value <= 0]
if invalid_service_timeouts:
    raise ImproperlyConfigured(
        "Servis timeout değerleri pozitif olmalıdır: " + ", ".join(invalid_service_timeouts)
    )

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = env_int("EMAIL_PORT", 25)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 30)
TECHNICAL_NOTIFICATION_PENDING_TIMEOUT = env_int(
    "TECHNICAL_NOTIFICATION_PENDING_TIMEOUT",
    300,
)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "UAV Center <noreply@uav-center.local>")

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured("EMAIL_USE_TLS ve EMAIL_USE_SSL aynı anda etkinleştirilemez.")
if EMAIL_TIMEOUT <= 0:
    raise ImproperlyConfigured("EMAIL_TIMEOUT pozitif bir değer olmalıdır.")
if TECHNICAL_NOTIFICATION_PENDING_TIMEOUT <= 0:
    raise ImproperlyConfigured(
        "TECHNICAL_NOTIFICATION_PENDING_TIMEOUT pozitif bir değer olmalıdır."
    )

NON_DELIVERY_EMAIL_BACKENDS = {
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
    "django.core.mail.backends.filebased.EmailBackend",
    "django.core.mail.backends.locmem.EmailBackend",
}
if IS_PRODUCTION and EMAIL_BACKEND in NON_DELIVERY_EMAIL_BACKENDS:
    raise ImproperlyConfigured(
        "Production ortamında teslimat yapan bir EMAIL_BACKEND açıkça tanımlanmalıdır."
    )

JIRA_SERVER = os.getenv("JIRA_SERVER", "").strip()
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD", "")
JIRA_PERSONAL_ACCESS_TOKEN = os.getenv("JIRA_PERSONAL_ACCESS_TOKEN", "")
JIRA_VERIFY_SSL = env_bool("JIRA_VERIFY_SSL", True)
JIRA_TIMEOUT = env_int("JIRA_TIMEOUT", 30)
JIRA_MEETING_PROJECT_KEY = os.getenv("JIRA_MEETING_PROJECT_KEY", "MOM")

if JIRA_SERVER:
    try:
        JIRA_SERVER = validated_http_url(
            JIRA_SERVER,
            setting_name="JIRA_SERVER",
            require_https=IS_PRODUCTION,
        )
    except InvalidServiceUrl as exc:
        raise ImproperlyConfigured(str(exc)) from exc
if JIRA_TIMEOUT <= 0:
    raise ImproperlyConfigured("JIRA_TIMEOUT pozitif bir değer olmalıdır.")

DOORS_DXL_BRIDGE = os.getenv(
    "DOORS_DXL_BRIDGE",
    str(BASE_DIR / "api" / "services" / "dxl" / "doors_connector_bridge.dxl"),
)
DOORS_TEMP_DIR = os.getenv("DOORS_TEMP_DIR") or None
DOORS_LOCK_TIMEOUT = env_int("DOORS_LOCK_TIMEOUT", 60)

if IS_PRODUCTION and OCR_ALLOW_MODEL_DOWNLOAD:
    raise ImproperlyConfigured("Production ortamında OCR_ALLOW_MODEL_DOWNLOAD=false olmalıdır.")
if IS_PRODUCTION and JIRA_SERVER and not JIRA_VERIFY_SSL:
    raise ImproperlyConfigured(
        "Production ortamında Jira bağlantısı için JIRA_VERIFY_SSL=true olmalıdır."
    )

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    []
    if IS_PRODUCTION
    else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
)
try:
    CORS_ALLOWED_ORIGINS = [
        validated_browser_origin(
            origin,
            setting_name="CORS_ALLOWED_ORIGINS",
            require_https=IS_PRODUCTION,
        )
        for origin in CORS_ALLOWED_ORIGINS
    ]
except InvalidServiceUrl as exc:
    raise ImproperlyConfigured(str(exc)) from exc
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (*default_headers, "idempotency-key")

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    []
    if IS_PRODUCTION
    else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
)
try:
    CSRF_TRUSTED_ORIGINS = [
        validated_browser_origin(
            origin,
            setting_name="CSRF_TRUSTED_ORIGINS",
            require_https=IS_PRODUCTION,
        )
        for origin in CSRF_TRUSTED_ORIGINS
    ]
except InvalidServiceUrl as exc:
    raise ImproperlyConfigured(str(exc)) from exc
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", IS_PRODUCTION)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", IS_PRODUCTION)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", IS_PRODUCTION)
SECURE_HSTS_SECONDS = env_int(
    "DJANGO_SECURE_HSTS_SECONDS",
    31_536_000 if IS_PRODUCTION else 0,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    IS_PRODUCTION,
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = os.getenv("DJANGO_SECURE_REFERRER_POLICY", "same-origin")
X_FRAME_OPTIONS = os.getenv("DJANGO_X_FRAME_OPTIONS", "DENY")

if IS_PRODUCTION:
    insecure_controls = [
        name
        for name, enabled in (
            ("DJANGO_SECURE_SSL_REDIRECT", SECURE_SSL_REDIRECT),
            ("DJANGO_SESSION_COOKIE_SECURE", SESSION_COOKIE_SECURE),
            ("DJANGO_CSRF_COOKIE_SECURE", CSRF_COOKIE_SECURE),
        )
        if not enabled
    ]
    if SECURE_HSTS_SECONDS <= 0:
        insecure_controls.append("DJANGO_SECURE_HSTS_SECONDS")
    if insecure_controls:
        raise ImproperlyConfigured(
            "Production güvenlik kontrolleri devre dışı bırakılamaz: "
            + ", ".join(insecure_controls)
        )

LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING" if APP_ENV == "test" else "INFO").strip().upper()
LOG_FORMAT = env_choice(
    "LOG_FORMAT",
    choices={"json", "text"},
    default="json" if IS_PRODUCTION else "text",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {"()": "config.logging.RequestContextFilter"},
        "redact": {"()": "config.logging.SensitiveDataFilter"},
    },
    "formatters": {
        "json": {"()": "config.logging.SafeJsonFormatter"},
        "text": {
            "()": "config.logging.SafeTextFormatter",
            "format": ("{asctime} {levelname} {name} request_id={request_id} {message}"),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_context", "redact"],
            "formatter": LOG_FORMAT,
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "api": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        *([] if IS_PRODUCTION else ["rest_framework.renderers.BrowsableAPIRenderer"]),
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}
