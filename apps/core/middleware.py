import contextvars
from django.utils.deprecation import MiddlewareMixin

_current_user = contextvars.ContextVar('current_user', default=None)
_current_ip = contextvars.ContextVar('current_ip', default=None)

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            _current_user.set(user)
        else:
            _current_user.set(None)

        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        _current_ip.set(ip)

    def process_response(self, request, response):
        # Reset context variables
        _current_user.set(None)
        _current_ip.set(None)
        return response

def get_current_user():
    try:
        return _current_user.get()
    except LookupError:
        return None

def get_current_ip():
    try:
        return _current_ip.get()
    except LookupError:
        return None
