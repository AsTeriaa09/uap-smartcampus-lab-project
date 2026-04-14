from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from main.views import (
    homepage, user_login, user_logout, 
    dashboard, cafeteria, transportation, events, ai,
    authority_login, authority_logout, authority_dashboard,
    authority_menu_list, authority_menu_add, authority_menu_edit, authority_menu_delete
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_login, name='login'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('cafeteria/', cafeteria, name='cafeteria'),
    path('transportation/', transportation, name='transportation'),
    path('events/', events, name='events'),
    path('ai/', ai, name='ai'),
    path('home/', homepage, name='home'),
    
    # Authority Management Portal
    path('authority/login/', authority_login, name='authority_login'),
    path('authority/logout/', authority_logout, name='authority_logout'),
    path('authority/dashboard/', authority_dashboard, name='authority_dashboard'),
    path('authority/menu/', authority_menu_list, name='authority_menu_list'),
    path('authority/menu/add/', authority_menu_add, name='authority_menu_add'),
    path('authority/menu/<int:item_id>/edit/', authority_menu_edit, name='authority_menu_edit'),
    path('authority/menu/<int:item_id>/delete/', authority_menu_delete, name='authority_menu_delete'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
