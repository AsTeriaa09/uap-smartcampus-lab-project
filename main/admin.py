from django.contrib import admin
from .models import MenuItem, ToDo


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'created_at']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available']
    ordering = ['category', 'name']


@admin.register(ToDo)
class ToDoAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
