from django.db import models
from django.contrib.auth.models import User


class Club(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=[
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('academic', 'Academic'),
        ('technology', 'Technology'),
        ('arts', 'Arts'),
        ('social', 'Social'),
    ])
    president = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='clubs/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Event(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events')
    event_date = models.DateField()
    event_time = models.TimeField()
    location = models.CharField(max_length=300)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['event_date', 'event_time']

    @property
    def registration_count(self):
        return self.registrations.count()


class EventRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    full_name = models.CharField(max_length=200, blank=True, default='')
    registration_number = models.CharField(max_length=50, blank=True, default='')
    edu_email = models.EmailField(blank=True, default='')
    department = models.CharField(max_length=100, blank=True, default='')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.full_name} ({self.registration_number}) registered for {self.event.title}"
