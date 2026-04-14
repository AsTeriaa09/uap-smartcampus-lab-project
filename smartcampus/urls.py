from django.contrib import admin
from django.urls import path
from main.views import homepage, user_login, user_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', homepage, name='home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
]
