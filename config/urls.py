from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import TemplateView
from core import views
urlpatterns=[path('admin/',admin.site.urls),path('administracao/',views.admin_overview,name='admin_overview'),path('',views.dashboard,name='dashboard'),path('entrar/',views.signin,name='login'),path('cadastro/',views.signup,name='signup'),path('sair/',LogoutView.as_view(),name='logout'),path('senha/',views.password_change,name='password_change'),path('recuperar/',views.recovery,name='recovery'),path('kits/',views.kits,name='kits'),path('kits/novo/',views.kit_edit,name='kit_new'),path('kits/<int:pk>/',views.kit_edit,name='kit_edit'),path('conferir/',views.inspect,name='inspect'),path('historico/',views.history,name='history'),path('conferencias/<int:pk>/',views.detail,name='detail'),path('conferencias/<int:pk>/imagem/',views.image,name='image'),path('conferencias/<int:pk>/revisao/',views.review,name='review'),path('exportar/',views.export,name='export'),path('sobre/',TemplateView.as_view(template_name='core/about.html'),name='about'),path('healthz',views.health)]
