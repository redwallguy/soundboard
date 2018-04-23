from django.contrib import admin

from .models import *

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    search_fields=['name']

@admin.register(Clip)
class ClipAdmin(admin.ModelAdmin):
    search_fields=['name','board__name']

@admin.register(Alias)
class AliasAdmin(admin.ModelAdmin):
    search_fields=['name','clip__name']

# Register your models here.
