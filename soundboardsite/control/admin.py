from django.contrib import admin

from .models import *

admin.site.site_header =  "Milton Administration. No posers allowed."
admin.site.site_title = "Milton Administration. No posers allowed."
admin.site.index_title = ""

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    search_fields=['name']

@admin.register(Clip)
class ClipAdmin(admin.ModelAdmin):
    search_fields=['name','board__name']
    list_display = ("name", "board") #shows name as well as board name on clip

@admin.register(Alias)
class AliasAdmin(admin.ModelAdmin):
    search_fields=['name','clip__name']
    raw_id_fields = ('clip',) #used to have clip show as input element rather than scroll-select box

# Register your models here.
