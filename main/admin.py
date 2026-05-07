from django.contrib import admin
from .models import MenuItem, Todo


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'created_at']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available']
    ordering = ['category', 'name']


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'todo_type', 'due_date', 'is_completed', 'created_at']
    list_filter = ['todo_type', 'is_completed']
    search_fields = ['title', 'description', 'user__username']
    ordering = ['due_date', 'created_at']
    readonly_fields = ['created_at']
