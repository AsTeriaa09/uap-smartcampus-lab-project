from django.contrib import admin
from .models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'todo_type', 'due_date', 'is_completed', 'created_at']
    list_filter = ['todo_type', 'is_completed']
    search_fields = ['title', 'description', 'user__username']
    ordering = ['due_date', 'created_at']
    readonly_fields = ['created_at']
