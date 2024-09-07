import logging
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Add a custom middleware for logging
class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log information about the incoming request
        logging.info(f"Incoming request: {request.method} {request.path}")
        logging.info(f"Headers: {request.headers}")

        response = self.get_response(request)

        # Log information about the response
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response headers: {response.headers}")

        return response