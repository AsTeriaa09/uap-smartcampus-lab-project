#!/usr/bin/env python3
"""
Setup script for UAP Admin Portal
Creates a superuser with known password if it doesn't exist
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcampus.settings')
django.setup()

from django.contrib.auth.models import User

# Create or update superuser
username = 'admin'
password = 'admin123'
email = 'admin@uap.edu'

try:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"✓ Updated existing superuser '{username}' with password '{password}'")
except User.DoesNotExist:
    User.objects.create_superuser(username, email, password)
    print(f"✓ Created new superuser '{username}' with password '{password}'")

print("\n" + "="*60)
print("UAP ADMIN PORTAL SETUP COMPLETE!")
print("="*60)
print(f"\nAdmin Portal URL: http://localhost:8000/uapadmin/login/")
print(f"Username: {username}")
print(f"Password: {password}")
print("\n" + "="*60)
