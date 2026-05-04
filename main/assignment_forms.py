from django import forms
from django.core.exceptions import ValidationError

from .assignment_models import Assignment, Course, Grade, Submission


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date', 'total_marks']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'due_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['due_date'].input_formats = [
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%dT%H:%M:%S',
        ]


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['marks', 'feedback']
        widgets = {
            'marks': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': 0},
            ),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, max_marks=None, **kwargs):
        self.max_marks = max_marks
        super().__init__(*args, **kwargs)

    def clean_marks(self):
        marks = self.cleaned_data['marks']
        if self.max_marks is not None and marks > self.max_marks:
            raise ValidationError(f'Marks cannot exceed maximum ({self.max_marks}).')
        return marks
