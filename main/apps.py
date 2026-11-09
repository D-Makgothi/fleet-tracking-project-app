from django.apps import AppConfig
from django.db.models.signals import post_migrate

# Import the models here


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    
  