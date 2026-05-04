"""
Assignment management UI and API (mixed CBV + FBV).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.edit import FormView

from .assignment_forms import AssignmentForm, CourseForm, GradeForm, SubmissionForm
from .assignment_models import Announcement, Assignment, Course, Grade, Submission
from .assignment_utils import (
    assignment_global_stats,
    calculate_average_percentage,
    calculate_gpa_four_point,
    overdue_assignments_queryset,
)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and not self.request.user.is_staff


class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'assignments/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        qs = Course.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = 'Courses'
        ctx['search_q'] = self.request.GET.get('q', '')
        stats = assignment_global_stats()
        ctx.update(
            {
                'dash_total_assignments': stats['total_assignments'],
                'dash_total_submissions': stats['total_submissions'],
                'dash_late_submissions': stats['late_submissions'],
                'dash_avg_marks': stats['average_marks'],
            },
        )
        qp = self.request.GET.copy()
        qp.pop('page', None)
        ctx['query_nopage'] = qp.urlencode()
        return ctx


class CourseCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'assignments/course_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Course created.')
        return reverse('assignments:course_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = 'Add course'
        return ctx


class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'assignments/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 10

    def get_queryset(self):
        cid = self.kwargs['course_id']
        self.course = get_object_or_404(Course, pk=cid)
        qs = (
            Assignment.objects.filter(course=self.course)
            .select_related('course', 'created_by')
            .order_by('due_date')
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        filt = self.request.GET.get('filter')
        if filt == 'overdue':
            qs = qs.filter(id__in=overdue_assignments_queryset(cid).values('id'))

        elif filt == 'upcoming':
            from django.utils import timezone

            qs = qs.filter(due_date__gte=timezone.now())

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.course
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = f'Assignments · {self.course.code}'
        ctx['announcements'] = Announcement.objects.filter(course=self.course)[:5]
        ctx['search_q'] = self.request.GET.get('q', '')
        ctx['current_filter'] = self.request.GET.get('filter', '')
        qp = self.request.GET.copy()
        qp.pop('page', None)
        ctx['query_nopage'] = qp.urlencode()
        return ctx


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'

    def get_queryset(self):
        return Assignment.objects.select_related('course', 'created_by')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = self.object
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = obj.title
        user = self.request.user
        if user.is_staff:
            ctx['submission'] = None
        else:
            ctx['submission'] = (
                Submission.objects.filter(assignment=obj, student=user)
                .select_related('grade')
                .first()
            )
        if user.is_staff:
            ctx['submissions'] = (
                Submission.objects.filter(assignment=obj)
                .select_related('student', 'grade')
                .order_by('-submitted_at')
            )
        return ctx


class AssignmentCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'assignments/assignment_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Assignment created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('assignments:assignment_detail', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        cid = self.request.GET.get('course')
        if cid:
            initial['course'] = cid
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = 'New assignment'
        return ctx


class SubmitAssignmentFormView(LoginRequiredMixin, StudentRequiredMixin, FormView):
    template_name = 'assignments/submit_assignment.html'
    form_class = SubmissionForm

    def dispatch(self, request, *args, **kwargs):
        self.assignment = get_object_or_404(
            Assignment.objects.select_related('course'),
            pk=self.kwargs['assignment_id'],
        )
        if Submission.objects.filter(assignment=self.assignment, student=request.user).exists():
            messages.info(request, 'You already submitted for this assignment.')
            return redirect('assignments:assignment_detail', pk=self.assignment.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        sub = Submission(assignment=self.assignment, student=self.request.user, file=form.cleaned_data['file'])
        sub.save()
        messages.success(self.request, 'Submission received.')
        return redirect('assignments:assignment_detail', pk=self.assignment.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assignment'] = self.assignment
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = 'Submit assignment'
        return ctx


class GradeSubmissionView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    template_name = 'assignments/grade_submission.html'
    form_class = GradeForm

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(
            Submission.objects.select_related('assignment', 'student'),
            pk=self.kwargs['submission_id'],
        )
        if Grade.objects.filter(submission=self.submission).exists():
            messages.info(request, 'This submission is already graded.')
            return redirect('assignments:assignment_detail', pk=self.submission.assignment_id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['max_marks'] = self.submission.assignment.total_marks
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['submission'] = self.submission
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = 'Grade submission'
        return ctx

    def form_valid(self, form):
        grade = form.save(commit=False)
        grade.submission = self.submission
        grade.save()
        messages.success(self.request, 'Grade saved.')
        return redirect('assignments:assignment_detail', pk=self.submission.assignment_id)


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    """Own submissions; GPA + late badges."""

    model = Submission
    template_name = 'assignments/student_dashboard.html'
    context_object_name = 'submissions'
    paginate_by = 10

    def get_queryset(self):
        return (
            Submission.objects.filter(student=self.request.user)
            .select_related('assignment', 'assignment__course', 'grade')
            .order_by('-submitted_at')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = 'My assignments'
        ctx['gpa_pct'] = calculate_average_percentage(self.request.user)
        ctx['gpa_four'] = calculate_gpa_four_point(self.request.user)
        st = assignment_global_stats()
        ctx.update(
            {
                'dash_total_assignments': st['total_assignments'],
                'dash_total_submissions': st['total_submissions'],
                'dash_late_submissions': st['late_submissions'],
                'dash_avg_marks': st['average_marks'],
            },
        )
        qp = self.request.GET.copy()
        qp.pop('page', None)
        ctx['query_nopage'] = qp.urlencode()
        return ctx


class TeacherDashboardView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Assignment
    template_name = 'assignments/teacher_dashboard.html'
    context_object_name = 'assignments'
    paginate_by = 15

    def get_queryset(self):
        qs = Assignment.objects.select_related('course', 'created_by').order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        course = self.request.GET.get('course')
        if course:
            qs = qs.filter(course_id=course)
        if self.request.GET.get('mine') == '1':
            qs = qs.filter(created_by=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_page'] = 'assignments'
        ctx['page_title'] = 'Teaching dashboard'
        ctx['courses'] = Course.objects.all().order_by('code')
        ctx['search_q'] = self.request.GET.get('q', '')
        ctx['courses_filter'] = self.request.GET.get('course', '')
        ctx['mine_only'] = self.request.GET.get('mine', '')
        st = assignment_global_stats()
        graded = Grade.objects.count()
        ctx.update(
            {
                **st,
                'graded_count': graded,
            },
        )
        qp = self.request.GET.copy()
        qp.pop('page', None)
        ctx['query_nopage'] = qp.urlencode()
        return ctx


@login_required
def api_assignments_list(request):
    """GET /api/assignments/ — JSON list."""
    qs = Assignment.objects.select_related('course').order_by('due_date')
    cid = request.GET.get('course_id')
    if cid:
        qs = qs.filter(course_id=cid)
    data = [
        {
            'id': a.id,
            'title': a.title,
            'course_code': a.course.code,
            'course_name': a.course.name,
            'due_date': a.due_date.isoformat(),
            'total_marks': a.total_marks,
            'is_overdue': a.is_overdue,
            'created_by': a.created_by.username,
        }
        for a in qs
    ]
    return JsonResponse({'count': len(data), 'results': data})
