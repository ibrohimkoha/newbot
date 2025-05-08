from django.contrib import admin
from .models import Anime, AnimeLanguage, RequiredChannel, Channel, Admin, User
# Register your models here.
admin.site.register(Anime)
admin.site.register(AnimeLanguage)
admin.site.register(RequiredChannel)
admin.site.register(Channel)
admin.site.register(Admin)
admin.site.register(User)