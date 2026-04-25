from django.db import models


class MenuItem(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(max_length=100, choices=[
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snacks', 'Snacks'),
        ('beverages', 'Beverages'),
    ])
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['category', 'name']


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
