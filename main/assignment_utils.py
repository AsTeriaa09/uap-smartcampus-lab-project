"""
Assignment / grading helpers: GPA, overdue, dashboard aggregates.
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Avg
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


def assignment_global_stats():
    """Counts used on teacher dashboard and APIs."""
    from .assignment_models import Assignment, Grade, Submission

    graded_ids = Grade.objects.values_list('submission_id', flat=True)
    pending_grade = Submission.objects.exclude(pk__in=graded_ids).count()
    return {
        'total_assignments': Assignment.objects.count(),
        'total_submissions': Submission.objects.count(),
        'late_submissions': Submission.objects.filter(is_late=True).count(),
        'average_marks': Grade.objects.aggregate(v=Avg('marks'))['v'],
        'pending_grades': pending_grade,
    }


def overdue_assignment_ids():
    """Primary keys of assignments past due (timezone-aware)."""
    from .assignment_models import Assignment

    now = timezone.now()
    return Assignment.objects.filter(due_date__lt=now).values_list('id', flat=True)


def overdue_assignments_queryset(course_id=None):
    from .assignment_models import Assignment

    qs = Assignment.objects.filter(due_date__lt=timezone.now()).select_related('course')
    if course_id:
        qs = qs.filter(course_id=course_id)
    return qs


def submissions_with_overdue_annotation(user):
    """Student submissions where the assignment is past due."""
    from .assignment_models import Submission

    overdue_ids = overdue_assignment_ids()
    return Submission.objects.filter(student=user, assignment_id__in=overdue_ids).select_related(
        'assignment',
        'assignment__course',
    )


def calculate_average_percentage(user: AbstractUser) -> Decimal | None:
    """Weighted by number of graded items; each item contributes pct = marks/total*100."""
    from .assignment_models import Grade

    graded = Grade.objects.filter(submission__student=user).select_related(
        'submission__assignment',
    )
    if not graded.exists():
        return None
    total_pct = Decimal('0')
    n = 0
    for g in graded:
        total = g.submission.assignment.total_marks
        if total <= 0:
            continue
        total_pct += (g.marks / Decimal(total)) * Decimal('100')
        n += 1
    if n == 0:
        return None
    return (total_pct / Decimal(n)).quantize(Decimal('0.01'))


def percentage_to_four_point_grade(pct: Decimal) -> Decimal:
    """Simple conversion table used by many campuses (approximation)."""
    if pct >= Decimal('93'):
        return Decimal('4.0')
    if pct >= Decimal('90'):
        return Decimal('3.7')
    if pct >= Decimal('87'):
        return Decimal('3.3')
    if pct >= Decimal('83'):
        return Decimal('3.0')
    if pct >= Decimal('80'):
        return Decimal('2.7')
    if pct >= Decimal('77'):
        return Decimal('2.3')
    if pct >= Decimal('73'):
        return Decimal('2.0')
    if pct >= Decimal('70'):
        return Decimal('1.7')
    if pct >= Decimal('67'):
        return Decimal('1.3')
    if pct >= Decimal('65'):
        return Decimal('1.0')
    return Decimal('0.0')


def calculate_gpa_four_point(user: AbstractUser) -> Decimal | None:
    pct = calculate_average_percentage(user)
    if pct is None:
        return None
    return percentage_to_four_point_grade(pct)
