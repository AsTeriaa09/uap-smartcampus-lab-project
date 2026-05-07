from django.db import models


class BusRoute(models.Model):
    route_name = models.CharField(max_length=200)
    departure_point = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    status = models.CharField(max_length=50, choices=[
        ('on_time', 'On Time'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    ], default='on_time')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.route_name} - {self.departure_point} to {self.destination}"

    class Meta:
        ordering = ['departure_time']
