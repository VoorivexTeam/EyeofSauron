from django.contrib import admin
from watch.models import Program, Target, HackeroneAPI, TelegramLog

# Register your models here.
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    empty_value_display = '-empty-'
    # fields = ('name', 'submission')
    list_display = ("id", "name", "bbp", "state", "platform")
    list_filter = ['state','platform', 'bbp', 'created_at', 'updated_at']
    ordering = ['id']
    search_fields = ['name']
    # raw_id_fields = ("platform",)
    
@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    empty_value_display = '-empty-'
    list_display = ("id", "title", "type", "scope", "program")
    list_filter = ['type', 'scope', 'created_at', 'updated_at','program__platform','program__bbp']
    ordering = ['id']
    search_fields = ['title', 'program__name']
    autocomplete_fields = ['program']
    

@admin.register(HackeroneAPI)
class HackeroneAPIAdmin(admin.ModelAdmin):
    list_display = ("username", "api_key")

@admin.register(TelegramLog)
class TelegramLoggerAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "bot_token")