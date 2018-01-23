from django.contrib import admin
from users.models import Passport,Recipient

admin.site.register(Passport) # 在admin中添加有关账户的编辑功能。
admin.site.register(Recipient) # 在admin中添加有关账户的编辑功能。

