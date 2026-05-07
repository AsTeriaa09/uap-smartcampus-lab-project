from django.contrib import admin
from .models import Club, Event, EventRegistration


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'president', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'president']
    ordering = ['name']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'club', 'event_date', 'event_time', 'location', 'is_active']
    list_filter = ['is_active', 'club']
    search_fields = ['title', 'location']
    ordering = ['event_date', 'event_time']


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'registration_number', 'event', 'user', 'registered_at']
    list_filter = ['event']
    search_fields = ['full_name', 'registration_number', 'edu_email']
    ordering = ['-registered_at']
