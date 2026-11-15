from datetime import timedelta

from django.urls import reverse_lazy

from settings.conf import BASE_DIR, BLOG_SECRET_KEY

SECRET_KEY = BLOG_SECRET_KEY

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.auths',
    'apps.blog',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "settings.urls"

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
            ],
        },
    },
]

AUTH_USER_MODEL = "auths.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),  
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True, 
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

UNFOLD = {
    "SITE_TITLE": "Blog Engine Admin",
    "SITE_HEADER": "Blog Dashboard",
    "SITE_SUBHEADER": "Advanced Management Panel",
    "SITE_SYMBOL": "newspaper",
    "COLORS": {
        "primary": {
            "50": "250 252 249",
            "100": "236 247 231",
            "200": "214 239 204",
            "300": "180 227 165",
            "400": "139 208 119",
            "500": "94 179 73",
            "600": "71 149 53",
            "700": "55 117 42",
            "800": "46 95 36",
            "900": "39 79 32",
            "950": "19 44 15",
        },
    },
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "COMMAND": {
        "search_models": True,
    },
    "SITE_DROPDOWN": [
        {"title": "Project GitHub", "icon": "code", "link": "https://github.com/NuranBerdaliyev/blog-api"},
        {"title": "Unfold Documentation", "icon": "description", "link": "https://unfoldadmin.com"},
    ],
        "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {
                    "title": "All",
                    "link": lambda request: str(reverse_lazy("admin:blog_post_changelist")),
                },
                {
                    "title": "Published",
                    "link": lambda request: f"{reverse_lazy('admin:blog_post_changelist')}?status__exact=published",
                },
                {
                    "title": "Drafts",
                    "link": lambda request: f"{reverse_lazy('admin:blog_post_changelist')}?status__exact=draft",
                },
            ],
        },
    ],
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": "Overview",
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    }
                ],
            },
            {
                "title": "Content",
                "items": [
                    {
                        "title": "Posts",
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_post_changelist"),
                        "badge": "apps.blog.callbacks.drafts_badge_callback",
                    },
                    {
                        "title": "Comments",
                        "icon": "comment",
                        "link": reverse_lazy("admin:blog_comment_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                    },
                    {
                        "title": "Tags",
                        "icon": "sell",
                        "link": reverse_lazy("admin:blog_tag_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Access",
                "items": [
                    {
                        "title": "Users",
                        "icon": "group",
                        "link": reverse_lazy("admin:auths_user_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Groups",
                        "icon": "verified_user",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
}
