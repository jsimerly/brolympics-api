from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse

@ensure_csrf_cookie
def set_csrf_token(request):
    return HttpResponse("CSRF cookie set")