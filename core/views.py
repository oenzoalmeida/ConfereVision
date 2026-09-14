import csv,hashlib,io,logging,time,secrets
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth.forms import SetPasswordForm
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm
from django.contrib.auth.models import User
from django.db.models import Count,Q
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST,require_GET
from .models import Kit,Inspection,Profile,Attempt
from .forms import SignupForm,KitForm,InspectForm
from .processing import process
from vision import DEFAULT_KIT
logger=logging.getLogger(__name__)

def limited(request,scope,identity='',limit=10):
    key=hashlib.sha256((scope+':'+identity).encode()).hexdigest()
    cutoff=timezone.now()-timedelta(minutes=15)
    Attempt.objects.filter(created__lt=cutoff).delete()
    if Attempt.objects.filter(key=key,created__gte=cutoff).count()>=limit:return True
    Attempt.objects.create(key=key)
    return False

def signin(request):
    if request.user.is_authenticated:return redirect('dashboard')
    form=AuthenticationForm(request,data=request.POST or None)
    if request.method=='POST':
        identity=request.POST.get('username','').strip().lower()
        if limited(request,'login',identity):form.add_error(None,'Muitas tentativas. Aguarde 15 minutos.')
        elif form.is_valid():
            login(request,form.get_user());return redirect('dashboard')
    return render(request,'registration/login.html',{'form':form})

def signup(request):
    if request.user.is_authenticated:return redirect('dashboard')
    form=SignupForm(request.POST or None)
    if request.method=='POST':
        if limited(request,'signup-global',limit=30):form.add_error(None,'Cadastro temporariamente limitado. Tente mais tarde.')
        elif form.is_valid():
            user=form.save()
            code=secrets.token_urlsafe(24)
            Profile.objects.create(user=user,recovery_hash=make_password(code))
            Kit.objects.create(owner=user,name='Demonstração geométrica',mode='geometric',composition=DEFAULT_KIT)
            Kit.objects.create(owner=user,name='Kit de mesa',mode='real',composition={'Garrafa':1,'Caneca / xícara':1})
            login(request,user)
            return render(request,'registration/recovery_code.html',{'code':code})
    return render(request,'registration/signup.html',{'form':form})

@login_required
def password_change(request):
    form=PasswordChangeForm(request.user,request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save();Profile.objects.update_or_create(user=user,defaults={'must_change_password':False})
        update_session_auth_hash(request,user);messages.success(request,'Senha atualizada.');return redirect('dashboard')
    return render(request,'registration/password.html',{'form':form})

@login_required
def dashboard(request):
    query=Inspection.objects.filter(owner=request.user)
    stats=query.aggregate(total=Count('id'),approved=Count('id',filter=Q(approved=True)),reviewed=Count('id',filter=~Q(human_review='pending')))
    return render(request,'core/dashboard.html',{'stats':stats,'recent':query.order_by('-created')[:5],'kit_count':Kit.objects.filter(owner=request.user).count()})

@login_required
def kits(request):
    return render(request,'core/kits.html',{'kits':Kit.objects.filter(owner=request.user).order_by('-created')})

@login_required
def kit_edit(request,pk=None):
    instance=get_object_or_404(Kit,pk=pk,owner=request.user) if pk else Kit(owner=request.user)
    form=KitForm(request.POST or None,instance=instance)
    if request.method=='POST' and form.is_valid():
        form.save();messages.success(request,'Kit salvo.');return redirect('kits')
    return render(request,'core/kit_form.html',{'form':form})

@login_required
def inspect(request):
    form=InspectForm(request.user,request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid():
        if limited(request,'inspect',str(request.user.pk),20):form.add_error(None,'Limite de 20 análises por 15 minutos. Aguarde.')
        else:
            try:
                start=time.monotonic()
                result=process(form.cleaned_data)
                obj=Inspection.objects.create(owner=request.user,kit_name=form.cleaned_data['kit'].name,mode=form.cleaned_data['kit'].mode,duration_ms=int((time.monotonic()-start)*1000),**result)
                return redirect('detail',pk=obj.pk)
            except (ValueError,RuntimeError) as exc:form.add_error(None,str(exc))
            except Exception:
                logger.exception('Falha no processamento')
                form.add_error(None,'Não foi possível processar o arquivo. Verifique o formato e tente outro.')
    return render(request,'core/inspect.html',{'form':form})

@login_required
def history(request):
    items=Inspection.objects.filter(owner=request.user).order_by('-created')[:100]
    return render(request,'core/history.html',{'items':items})

@login_required
def detail(request,pk):
    item=get_object_or_404(Inspection,pk=pk,owner=request.user)
    return render(request,'core/detail.html',{'item':item})

@login_required
@require_GET
def image(request,pk):
    item=get_object_or_404(Inspection,pk=pk,owner=request.user)
    response=HttpResponse(bytes(item.image),content_type='image/jpeg')
    response['Cache-Control']='private, no-store'
    response['X-Content-Type-Options']='nosniff'
    return response

@login_required
@require_POST
def review(request,pk):
    item=get_object_or_404(Inspection,pk=pk,owner=request.user)
    value=request.POST.get('review')
    if value in ['correct','incorrect']:
        item.human_review=value;item.save(update_fields=['human_review'])
    return redirect('detail',pk=pk)

@login_required
def export(request):
    result=io.StringIO();result.write('\ufeff')
    writer=csv.writer(result,delimiter=';')
    writer.writerow(['ID','Data','Kit','Resultado','Revisão humana'])
    def safe(s):return "'"+s if s.lstrip().startswith(('=','+','-','@')) else s
    for item in Inspection.objects.filter(owner=request.user).order_by('-created')[:5000]:
        writer.writerow([item.pk,item.created.isoformat(),safe(item.kit_name),'Compatível' if item.approved else 'Revisar',item.get_human_review_display()])
    response=HttpResponse(result.getvalue(),content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="conferencias.csv"'
    return response

@login_required
def admin_overview(request):
    if not request.user.is_superuser:return HttpResponse('Acesso restrito ao administrador.',status=403)
    return render(request,'core/admin_overview.html',{'users':User.objects.count(),'kits':Kit.objects.count(),'inspections':Inspection.objects.count(),'pending':Inspection.objects.filter(human_review='pending').count()})

def health(request):
    from django.db import connection
    try:
        with connection.cursor() as cursor:cursor.execute('SELECT 1')
        return JsonResponse({'status':'ok'})
    except Exception:return JsonResponse({'status':'unavailable'},status=503)


def recovery(request):
    form=SetPasswordForm(User(),request.POST or None)
    error=None
    if request.method=='POST':
        username=request.POST.get('username','').strip()
        if limited(request,'recovery',username.lower(),5):error='Muitas tentativas. Aguarde 15 minutos.'
        else:
            user=User.objects.filter(username=username,is_active=True).first()
            profile=Profile.objects.filter(user=user).first() if user else None
            valid=profile and profile.recovery_hash and check_password(request.POST.get('code',''),profile.recovery_hash)
            if not valid:error='Usuário ou código de recuperação inválido.'
            else:
                form=SetPasswordForm(user,request.POST)
                if form.is_valid():
                    user=form.save()
                    code=secrets.token_urlsafe(24)
                    profile.recovery_hash=make_password(code);profile.must_change_password=False
                    profile.save()
                    return render(request,'registration/recovery_code.html',{'code':code})
    return render(request,'registration/recovery.html',{'form':form,'error':error})
