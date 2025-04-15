from django.db import models
from django.utils import timezone
# Create your models here.



class Program(models.Model):
    name = models.CharField(max_length=500)
    submission = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    class PLATFORMS(models.TextChoices):
        Hackerone = "hackerone"
        Bugcrowd = "bugcrowd"
        Intigrity = "intigrity"
        Others = "others"

    platform = models.CharField(
        max_length=30,
        choices=PLATFORMS.choices,
        default= "others"
    )
    bbp = models.BooleanField()
    state = models.CharField(max_length=10, blank=True, null=True)
    # class Meta:
    #     verbose_name = "program"
    #     verbose_name_plural = "program"
    #     ordering = ['name']
    def __str__(self):
        return self.name
    
class Target(models.Model):
    title = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    class TYPES(models.TextChoices):
        cidr = "cidr"
        android = "android"
        ios = "ios"
        website = "website"
        iot = "iot"
        api = "api"
        hardware = "hardware"
        other = "other"
        source_code = "source_code"
        exe = "exe"

    type = models.CharField(
        max_length=15,
        choices=TYPES.choices,
        default="website")
    scope = models.BooleanField(blank=True)
    
    program = models.ForeignKey(
        Program,
        related_name="scopes",
        on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title
    

class TelegramLog(models.Model):
    chat_id = models.CharField(max_length=50, unique=True)
    bot_token = models.CharField(max_length=100, unique=True)
    # logger = models.BooleanField(default=False)
    def __str__(self):
        return f"Logger {self.chat_id}"
    
class HackeroneAPI(models.Model):
    username = models.CharField(max_length=50, unique=True)
    api_key = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return f"Username {self.username}"