from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from main.views import (
    homepage, user_login, user_register, user_logout,
    dashboard, cafeteria, transportation, events, ai,
    ai_chat_api,
    authority_login, authority_logout, authority_dashboard,
    authority_menu_list, authority_menu_add, authority_menu_edit, authority_menu_delete,
    admin_login, admin_logout, admin_dashboard,
    admin_menu_list, admin_menu_add, admin_menu_edit, admin_menu_delete,
    admin_bus_routes, admin_bus_add, admin_bus_edit, admin_bus_delete,
    admin_clubs, admin_club_add, admin_club_edit, admin_club_delete,
    admin_events, admin_event_add, admin_event_edit, admin_event_delete, admin_event_registrations,
    add_to_cart, update_cart_item, remove_from_cart, cart_view, confirm_order, order_now, my_orders,
    admin_orders, admin_order_detail, admin_order_status,
    register_for_event, unregister_from_event, my_registered_events,
    todo_add, todo_edit, todo_delete, todo_toggle
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login')),
    path('login/', user_login, name='login'),
    path('register/', user_register, name='register'),
    path('logout/', user_logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('cafeteria/', cafeteria, name='cafeteria'),
    path('transportation/', transportation, name='transportation'),
    path('events/', events, name='events'),
    path('events/register/<int:event_id>/', register_for_event, name='register_for_event'),
    path('events/unregister/<int:event_id>/', unregister_from_event, name='unregister_from_event'),
    path('events/my-registrations/', my_registered_events, name='my_registered_events'),
    path('ai/', ai, name='ai'),
    path('ai/chat/', ai_chat_api, name='ai_chat_api'),
    path('home/', homepage, name='home'),
    
    # Authority Management Portal
    path('authority/login/', authority_login, name='authority_login'),
    path('authority/logout/', authority_logout, name='authority_logout'),
    path('authority/dashboard/', authority_dashboard, name='authority_dashboard'),
    path('authority/menu/', authority_menu_list, name='authority_menu_list'),
    path('authority/menu/add/', authority_menu_add, name='authority_menu_add'),
    path('authority/menu/<int:item_id>/edit/', authority_menu_edit, name='authority_menu_edit'),
    path('authority/menu/<int:item_id>/delete/', authority_menu_delete, name='authority_menu_delete'),
    
    # UAP Admin Portal
    path('uapadmin/', lambda request: redirect('admin_login')),
    path('uapadmin/login/', admin_login, name='admin_login'),
    path('uapadmin/logout/', admin_logout, name='admin_logout'),
    path('uapadmin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('uapadmin/menu/', admin_menu_list, name='admin_menu_list'),
    path('uapadmin/menu/add/', admin_menu_add, name='admin_menu_add'),
    path('uapadmin/menu/<int:item_id>/edit/', admin_menu_edit, name='admin_menu_edit'),
    path('uapadmin/menu/<int:item_id>/delete/', admin_menu_delete, name='admin_menu_delete'),
    path('uapadmin/bus/', admin_bus_routes, name='admin_bus_routes'),
    path('uapadmin/bus/add/', admin_bus_add, name='admin_bus_add'),
    path('uapadmin/bus/<int:route_id>/edit/', admin_bus_edit, name='admin_bus_edit'),
    path('uapadmin/bus/<int:route_id>/delete/', admin_bus_delete, name='admin_bus_delete'),
    path('uapadmin/clubs/', admin_clubs, name='admin_clubs'),
    path('uapadmin/clubs/add/', admin_club_add, name='admin_club_add'),
    path('uapadmin/clubs/<int:club_id>/edit/', admin_club_edit, name='admin_club_edit'),
    path('uapadmin/clubs/<int:club_id>/delete/', admin_club_delete, name='admin_club_delete'),
    path('uapadmin/events/', admin_events, name='admin_events'),
    path('uapadmin/events/add/', admin_event_add, name='admin_event_add'),
    path('uapadmin/events/<int:event_id>/edit/', admin_event_edit, name='admin_event_edit'),
    path('uapadmin/events/<int:event_id>/delete/', admin_event_delete, name='admin_event_delete'),
    path('uapadmin/events/<int:event_id>/registrations/', admin_event_registrations, name='admin_event_registrations'),
    
    # User Cart & Orders
    path('cafeteria/add-to-cart/<int:item_id>/', add_to_cart, name='add_to_cart'),
    path('cafeteria/cart/', cart_view, name='cart_view'),
    path('cafeteria/cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cafeteria/cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cafeteria/order/confirm/', confirm_order, name='confirm_order'),
    path('cafeteria/order-now/<int:item_id>/', order_now, name='order_now'),
    path('orders/', my_orders, name='my_orders'),

    path('todos/add/', todo_add, name='todo_add'),
    path('todos/<int:todo_id>/edit/', todo_edit, name='todo_edit'),
    path('todos/<int:todo_id>/delete/', todo_delete, name='todo_delete'),
    path('todos/<int:todo_id>/toggle/', todo_toggle, name='todo_toggle'),
    
    # Admin Orders
    path('uapadmin/orders/', admin_orders, name='admin_orders'),
    path('uapadmin/orders/<int:order_id>/', admin_order_detail, name='admin_order_detail'),
    path('uapadmin/orders/<int:order_id>/status/', admin_order_status, name='admin_order_status'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
