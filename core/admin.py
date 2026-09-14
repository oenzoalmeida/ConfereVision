from django.contrib import admin
from .models import Kit,Inspection,Profile
admin.site.site_header='ConfereVision • Administração'
admin.site.site_title='ConfereVision Admin'
admin.site.index_title='Usuários e operação'
@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    list_display=['name','owner','mode','created']
    list_filter=['mode']
    search_fields=['name','owner__username']
@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display=['id','owner','kit_name','approved','human_review','created']
    list_filter=['approved','human_review','mode']
    exclude=['image']
    readonly_fields=['owner','kit_name','mode','created','source','approved','details','timeline','duration_ms']
    def has_add_permission(self,request):return False
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display=['user','must_change_password']
