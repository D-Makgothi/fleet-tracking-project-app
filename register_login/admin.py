from django.contrib import admin
from .models import RegistryModel, ClientModel, SiteModel

# Register your models here.

admin.site.register(RegistryModel)
admin.site.register(ClientModel)
admin.site.register(SiteModel)