from django.contrib import admin
from .models import BusRoute


@admin.register(BusRoute)
class BusRouteAdmin(admin.ModelAdmin):
    list_display = ['route_name', 'departure_point', 'destination', 'departure_time', 'arrival_time', 'status', 'is_active']
    list_filter = ['status', 'is_active']
    search_fields = ['route_name', 'departure_point', 'destination']
    ordering = ['departure_time']
