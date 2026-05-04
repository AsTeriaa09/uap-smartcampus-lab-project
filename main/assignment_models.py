"""
Assignment management domain models (Smart Campus).
"""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=32, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class Assignment(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    total_marks = models.PositiveSmallIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_assignments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.title} ({self.course.code})"

    @property
    def is_overdue(self) -> bool:
        return timezone.now() > self.due_date


class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignment_submissions',
    )
    file = models.FileField(upload_to='assignment_submissions/%Y/%m/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(
                fields=['assignment', 'student'],
                name='uniq_assignment_submission_per_student',
            ),
        ]

    def __str__(self):
        return f"{self.student.username} → {self.assignment.title}"

    def recalculate_late(self) -> None:
        self.is_late = self.submitted_at > self.assignment.due_date

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recalculate_late()
        Submission.objects.filter(pk=self.pk).update(is_late=self.is_late)


class Grade(models.Model):
    submission = models.OneToOneField(
        Submission,
        on_delete=models.CASCADE,
        related_name='grade',
    )
    marks = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-graded_at']

    def __str__(self):
        return f"Grade {self.marks} — {self.submission}"


class Announcement(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='announcements',
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.course.code})"
