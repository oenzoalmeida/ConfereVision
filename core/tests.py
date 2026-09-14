from unittest.mock import patch
from django.test import TestCase,Client,override_settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Kit,Inspection,Profile
from vision import DEFAULT_KIT

@override_settings(STORAGES={'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'},'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'}})
class AccessTests(TestCase):
    def setUp(self):
        self.a=User.objects.create_user('alice','alice@example.com','Example-safe-password-123')
        self.b=User.objects.create_user('bruno','bruno@example.com','Example-safe-password-456')
        self.admin=User.objects.create_superuser('admin','admin@example.com','Example-safe-password-789')
        self.kit=Kit.objects.create(owner=self.a,name='Kit privado',mode='geometric',composition=DEFAULT_KIT)
        self.item=Inspection.objects.create(owner=self.a,kit_name='Kit privado',mode='geometric',image=b'abc',details=[])
    def test_anonymous_protected(self):
        for url in ['/','/kits/','/historico/','/administracao/',f'/conferencias/{self.item.pk}/imagem/']:
            self.assertEqual(self.client.get(url).status_code,302)
    def test_customer_denied_admin(self):
        self.client.force_login(self.a)
        self.assertEqual(self.client.get('/administracao/').status_code,403)
        self.assertEqual(self.client.get('/admin/').status_code,302)
    def test_cross_user_access(self):
        self.client.force_login(self.b)
        for url in [f'/kits/{self.kit.pk}/',f'/conferencias/{self.item.pk}/',f'/conferencias/{self.item.pk}/imagem/']:
            self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.post(f'/conferencias/{self.item.pk}/revisao/',{'review':'correct'}).status_code,404)
        self.assertNotContains(self.client.get('/historico/'),'Kit privado')
        self.assertNotContains(self.client.get('/exportar/'),'Kit privado')
    def test_cannot_inspect_others_kit(self):
        self.client.force_login(self.b)
        response=self.client.post('/conferir/',{'kit':self.kit.pk,'source':'correct'})
        self.assertContains(response,'Faça uma escolha válida')
        self.assertEqual(Inspection.objects.count(),1)
    def test_csrf(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.a)
        self.assertEqual(c.post(f'/conferencias/{self.item.pk}/revisao/',{'review':'correct'}).status_code,403)
    def test_registration_no_escalation(self):
        response=self.client.post('/cadastro/',{'username':'newuser','email':'new@example.com','password1':'Unique-safe-password-2026','password2':'Unique-safe-password-2026','is_staff':'1','is_superuser':'1'})
        self.assertEqual(response.status_code,200)
        user=User.objects.get(username='newuser')
        self.assertFalse(user.is_staff);self.assertFalse(user.is_superuser)
        self.assertTrue(user.profile.recovery_hash)
        self.assertEqual(Kit.objects.filter(owner=user).count(),2)
    def test_password_change_gate(self):
        Profile.objects.create(user=self.admin,must_change_password=True)
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get('/admin/'),'/senha/')
    def test_admin_pages(self):
        self.client.force_login(self.admin)
        for url in ['/administracao/','/admin/','/admin/auth/user/','/admin/core/inspection/']:
            self.assertEqual(self.client.get(url).status_code,200,url)
    def test_disabled_user_revoked(self):
        self.client.force_login(self.a);self.a.is_active=False;self.a.save()
        self.assertEqual(self.client.get('/').status_code,302)
    def test_demo_end_to_end(self):
        self.client.force_login(self.a)
        for source,expected in [('correct',True),('missing',False),('extra',False)]:
            response=self.client.post('/conferir/',{'kit':self.kit.pk,'source':source})
            self.assertEqual(response.status_code,302)
            item=Inspection.objects.latest('id');self.assertEqual(item.approved,expected)
            self.assertEqual(self.client.get(response.url).status_code,200)
            self.assertEqual(self.client.get(f'/conferencias/{item.pk}/imagem/')['Content-Type'],'image/jpeg')
    def test_invalid_upload(self):
        self.client.force_login(self.a)
        response=self.client.post('/conferir/',{'kit':self.kit.pk,'source':'image','file':SimpleUploadedFile('bad.png',b'not an image')})
        self.assertContains(response,'Imagem inválida')
    def test_recovery_rotates_code(self):
        Profile.objects.create(user=self.a,recovery_hash=make_password('secret-recovery-code'))
        response=self.client.post('/recuperar/',{'username':'alice','code':'secret-recovery-code','new_password1':'Replacement-password-2026','new_password2':'Replacement-password-2026'})
        self.assertContains(response,'Guarde seu código')
        self.a.refresh_from_db();self.assertTrue(self.a.check_password('Replacement-password-2026'))
        response=self.client.post('/recuperar/',{'username':'alice','code':'secret-recovery-code','new_password1':'Another-safe-password-2026','new_password2':'Another-safe-password-2026'})
        self.assertContains(response,'inválido')
    def test_login_throttle(self):
        for i in range(11):response=self.client.post('/entrar/',{'username':'alice','password':'wrong'})
        self.assertContains(response,'Muitas tentativas')
    def test_csv_formula_neutralized(self):
        self.item.kit_name='=1+1';self.item.save();self.client.force_login(self.a)
        self.assertIn("'=1+1",self.client.get('/exportar/').content.decode('utf-8-sig'))
    def test_every_customer_page_renders(self):
        self.client.force_login(self.a)
        for url in ['/','/kits/','/kits/novo/','/conferir/','/historico/','/senha/','/sobre/']:
            self.assertEqual(self.client.get(url).status_code,200,url)

    def test_admin_login_throttle(self):
        for i in range(11):response=self.client.post('/admin/login/',{'username':'admin','password':'wrong'})
        self.assertEqual(response.status_code,429)
