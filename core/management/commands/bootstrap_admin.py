import os,secrets
from pathlib import Path
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from core.models import Profile,Kit
from vision import DEFAULT_KIT
class Command(BaseCommand):
    help='Cria admin inicial sem modificar contas existentes. Senha nunca entra no código.'
    def handle(self,*args,**kwargs):
        username=os.getenv('ADMIN_USERNAME','administrador')
        if User.objects.filter(username=username).exists():
            self.stdout.write('Conta já existe; nenhuma credencial alterada.');return
        password=os.getenv('ADMIN_PASSWORD')
        generated=not password
        if generated:password=secrets.token_urlsafe(20)
        validate_password(password)
        user=User.objects.create_superuser(username,os.getenv('ADMIN_EMAIL','admin@conferevision.invalid'),password)
        recovery=secrets.token_urlsafe(24)
        Profile.objects.create(user=user,must_change_password=True,recovery_hash=make_password(recovery))
        Kit.objects.create(owner=user,name='Demonstração geométrica',mode='geometric',composition=DEFAULT_KIT)
        Kit.objects.create(owner=user,name='Kit de mesa',mode='real',composition={'Garrafa':1,'Caneca / xícara':1})
        if generated:
            path=Path('ACESSO_ADMIN.txt')
            path.write_text(f'ConfereVision — acesso local\nUsuário: {username}\nIdentificador de e-mail: {user.email} (não é uma caixa postal)\nSenha inicial: {password}\nCódigo de recuperação: {recovery}\nTroca obrigatória no primeiro acesso.\n',encoding='utf-8')
            path.chmod(0o600)
            self.stdout.write('Administrador criado. Credenciais em ACESSO_ADMIN.txt; guarde fora do repositório.')
        else:self.stdout.write('Administrador criado com a senha fornecida no ambiente.')
