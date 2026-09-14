from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Kit
from detector import PRODUCTS
from vision import COLORS, SHAPES

class SignupForm(UserCreationForm):
    email=forms.EmailField(label='E-mail')
    class Meta:
        model=User
        fields=['username','email','password1','password2']
    def clean_email(self):
        email=self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():raise forms.ValidationError('Não foi possível usar este e-mail. Utilize outro ou contate o administrador.')
        return email

class KitForm(forms.ModelForm):
    class Meta:
        model=Kit
        fields=['name','mode']
        labels={'name':'Nome do kit','mode':'Tipo de detecção'}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for i,label in enumerate(list(PRODUCTS.values())+[f'{c} / {s}' for c in COLORS for s in SHAPES]):
            self.fields[f'item_{i}']=forms.IntegerField(label=label,min_value=0,max_value=20,required=False,initial=self.instance.composition.get(label,0) if self.instance.pk else 0)
    def clean(self):
        values=super().clean()
        allowed=list(PRODUCTS.values()) if values.get('mode')=='real' else [f'{c} / {s}' for c in COLORS for s in SHAPES]
        composition={f.label:values.get(k) for k,f in self.fields.items() if k.startswith('item_') and values.get(k) and f.label in allowed}
        if not composition:raise forms.ValidationError('Selecione pelo menos um item do tipo de detecção escolhido.')
        if sum(composition.values())>30:raise forms.ValidationError('Limite de 30 objetos por kit.')
        self.instance.composition=composition
        return values

class InspectForm(forms.Form):
    kit=forms.ModelChoiceField(queryset=Kit.objects.none(),label='Kit esperado')
    source=forms.ChoiceField(label='Origem',choices=[('image','Imagem / foto'),('video','Vídeo'),('correct','Demonstração completa'),('missing','Demonstração com falta'),('extra','Demonstração com excedente')])
    file=forms.FileField(label='Arquivo',required=False,widget=forms.ClearableFileInput(attrs={'accept':'image/jpeg,image/png,video/mp4,video/x-msvideo,video/quicktime'}))
    def __init__(self,user,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['kit'].queryset=Kit.objects.filter(owner=user)
    def clean(self):
        values=super().clean()
        file=values.get('file')
        if values.get('source') in ['image','video'] and not file:raise forms.ValidationError('Selecione um arquivo.')
        if file and file.size>30*1024*1024:raise forms.ValidationError('O arquivo deve ter até 30 MB.')
        if values.get('source') not in ['image','video'] and values.get('kit') and values['kit'].mode!='geometric':raise forms.ValidationError('A demonstração sintética exige um kit geométrico. Para objetos reais, envie uma foto ou vídeo.')
        return values
