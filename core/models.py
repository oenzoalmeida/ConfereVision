from django.conf import settings
from django.db import models

class Profile(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    must_change_password=models.BooleanField(default=False)
    recovery_hash=models.CharField(max_length=128,blank=True)

class Kit(models.Model):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    mode=models.CharField(max_length=12,choices=[('real','Objetos reais'),('geometric','Geométrico')],default='real')
    composition=models.JSONField(default=dict)
    created=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Inspection(models.Model):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    kit_name=models.CharField(max_length=100)
    mode=models.CharField(max_length=12)
    created=models.DateTimeField(auto_now_add=True)
    source=models.CharField(max_length=200)
    approved=models.BooleanField(default=False)
    details=models.JSONField(default=list)
    timeline=models.JSONField(default=list)
    image=models.BinaryField()
    duration_ms=models.PositiveIntegerField(default=0)
    human_review=models.CharField(max_length=12,choices=[('pending','Pendente'),('correct','Correto'),('incorrect','Incorreto')],default='pending')

class Attempt(models.Model):
    key=models.CharField(max_length=64,db_index=True)
    created=models.DateTimeField(auto_now_add=True)
