from invest.signals import set_user


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_user(request.user if request.user.is_authenticated else None)
        response = self.get_response(request)
        return response
