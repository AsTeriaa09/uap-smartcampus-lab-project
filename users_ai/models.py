from django.db import models
from django.contrib.auth.models import User


class Todo(models.Model):
    TYPE_CHOICES = [
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    todo_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='assignment')
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        return self.title
