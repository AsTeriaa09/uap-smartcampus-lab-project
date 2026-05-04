from django.contrib import admin
from .assignment_models import Announcement, Assignment, Course, Grade, Submission
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


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'created_at']
    search_fields = ['code', 'name', 'description']
    list_filter = ['created_at']
    ordering = ['code']
    readonly_fields = ['created_at']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'due_date', 'total_marks', 'created_by', 'created_at']
    list_filter = ['course', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'course__code', 'course__name']
    ordering = ['due_date']
    readonly_fields = ['created_at']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'submitted_at', 'is_late']
    list_filter = ['is_late', 'submitted_at', 'assignment__course']
    search_fields = ['student__username', 'assignment__title']
    ordering = ['-submitted_at']
    readonly_fields = ['submitted_at', 'is_late']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['submission', 'marks', 'graded_at']
    search_fields = ['submission__assignment__title', 'submission__student__username', 'feedback']
    list_filter = ['graded_at']
    ordering = ['-graded_at']
    readonly_fields = ['graded_at']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'created_at']
    search_fields = ['title', 'message', 'course__code']
    list_filter = ['course', 'created_at']
    ordering = ['-created_at']
