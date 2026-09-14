from django.shortcuts import redirect
class PasswordChangeMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        if request.user.is_authenticated and request.path not in ['/senha/','sair/','/sair/'] and not request.path.startswith('/static/'):
            from .models import Profile
            if Profile.objects.filter(user=request.user,must_change_password=True).exists():return redirect('password_change')
        return self.get_response(request)

class AdminLoginThrottleMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        if request.method=='POST' and request.path=='/admin/login/':
            from .views import limited
            from django.http import HttpResponse
            if limited(request,'admin-login',request.POST.get('username','').strip().lower(),10):
                return HttpResponse('Muitas tentativas. Aguarde 15 minutos e tente novamente.',status=429)
        return self.get_response(request)
