from .defaults import *  # noqa
from website import settings as osf_settings


DEBUG = osf_settings.DEBUG_MODE
VARNISH_SERVERS = ['http://127.0.0.1:8080']
ENABLE_VARNISH = False
ENABLE_ESI = False
CORS_ORIGIN_ALLOW_ALL = True

# Uncomment to get real tracebacks while testing
# DEBUG_PROPAGATE_EXCEPTIONS = True

if DEBUG:
    INSTALLED_APPS += ('debug_toolbar', 'nplusone.ext.django',)
    MIDDLEWARE += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'nplusone.ext.django.NPlusOneMiddleware',
    )
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda _: True,
    }
    ALLOWED_HOSTS.append('localhost')

    # django-silk
    INSTALLED_APPS += ('silk',)
    MIDDLEWARE += (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'silk.middleware.SilkyMiddleware',
    )


REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'user': '1000000/second',
    'non-cookie-auth': '1000000/second',
    'add-contributor': '1000000/second',
    'create-guid': '1000000/second',
    'root-anon-throttle': '1000000/second',
    'test-user': '2/hour',
    'test-anon': '1/hour',
    'send-email': '2/minute',
    'burst': '10/second',
}

REST_FRAMEWORK['ALLOWED_VERSIONS'] = (
    '2.0',
    '2.1',
    '2.2',
    '2.3',
    '2.4',
    '2.5',
    '2.6',
    '2.7',
    '2.8',
    '2.9',
    '2.10',
    '2.11',
    '2.12',
    '2.13',
    '2.14',
    '2.15',
    '2.16',
    '2.17',
    '2.18',
    '2.19',
    '2.20'
)

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost'
]