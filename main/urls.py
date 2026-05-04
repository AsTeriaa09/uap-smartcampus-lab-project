from django.urls import path

from . import assignment_views as av

app_name = 'assignments'

urlpatterns = [
    path('courses/', av.CourseListView.as_view(), name='course_list'),
    path('courses/add/', av.CourseCreateView.as_view(), name='course_add'),
    path(
        'courses/<int:course_id>/assignments/',
        av.AssignmentListView.as_view(),
        name='assignment_list',
    ),
    path('dashboard/student/', av.StudentDashboardView.as_view(), name='student_dashboard'),
    path('dashboard/teacher/', av.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('create/', av.AssignmentCreateView.as_view(), name='assignment_create'),
    path('submissions/<int:submission_id>/grade/', av.GradeSubmissionView.as_view(), name='grade_submission'),
    path('<int:assignment_id>/submit/', av.SubmitAssignmentFormView.as_view(), name='submit_assignment'),
    path('<int:pk>/', av.AssignmentDetailView.as_view(), name='assignment_detail'),
]
