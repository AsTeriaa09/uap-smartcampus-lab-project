import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder

from .models import Club, Event, EventRegistration


@login_required
def events(request):
    clubs = Club.objects.filter(is_active=True)
    all_events = Event.objects.filter(is_active=True).order_by('event_date', 'event_time')
    user_registered_event_ids = set(
        EventRegistration.objects.filter(user=request.user).values_list('event_id', flat=True)
    )
    clubs_data = []
    for club in clubs:
        clubs_data.append({
            'id': club.id,
            'name': club.name,
            'description': club.description,
            'category': club.category,
            'category_display': club.get_category_display(),
            'president': club.president,
            'contact_email': club.contact_email,
            'logo': club.logo.url if club.logo else None,
            'is_active': club.is_active,
        })
    events_data = []
    for event in all_events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'club_id': event.club_id,
            'club_name': event.club.name if event.club else None,
            'event_date': event.event_date.isoformat(),
            'event_time': event.event_time.strftime('%H:%M:%S'),
            'location': event.location,
            'image': event.image.url if event.image else None,
            'is_active': event.is_active,
            'is_registered': event.id in user_registered_event_ids,
            'registration_count': event.registration_count,
        })
    return render(request, 'events.html', {
        'active_page': 'events',
        'page_title': 'Events & Clubs',
        'clubs': clubs,
        'events': all_events,
        'clubs_json': json.dumps(clubs_data, cls=DjangoJSONEncoder),
        'events_json': json.dumps(events_data, cls=DjangoJSONEncoder),
        'user_registered_event_ids': user_registered_event_ids,
    })


@login_required
def register_for_event(request, event_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    event = get_object_or_404(Event, id=event_id, is_active=True)
    if EventRegistration.objects.filter(user=request.user, event=event).exists():
        return JsonResponse({'success': False, 'message': 'You are already registered for this event', 'is_registered': True, 'registration_count': event.registration_count})
    full_name = request.POST.get('full_name', '').strip()
    registration_number = request.POST.get('registration_number', '').strip()
    edu_email = request.POST.get('edu_email', '').strip()
    department = request.POST.get('department', '').strip()
    if not full_name:
        return JsonResponse({'success': False, 'message': 'Full name is required'})
    if not registration_number:
        return JsonResponse({'success': False, 'message': 'Registration number is required'})
    if not edu_email:
        return JsonResponse({'success': False, 'message': 'Educational email is required'})
    if not department:
        return JsonResponse({'success': False, 'message': 'Department is required'})
    EventRegistration.objects.create(
        user=request.user, event=event, full_name=full_name,
        registration_number=registration_number, edu_email=edu_email, department=department
    )
    return JsonResponse({'success': True, 'message': f'Successfully registered for "{event.title}"', 'is_registered': True, 'registration_count': event.registration_count})


@login_required
def unregister_from_event(request, event_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    event = get_object_or_404(Event, id=event_id, is_active=True)
    registration = EventRegistration.objects.filter(user=request.user, event=event).first()
    if not registration:
        return JsonResponse({'success': False, 'message': 'You are not registered for this event', 'is_registered': False, 'registration_count': event.registration_count})
    registration.delete()
    return JsonResponse({'success': True, 'message': f'Successfully unregistered from "{event.title}"', 'is_registered': False, 'registration_count': event.registration_count})


@login_required
def my_registered_events(request):
    registrations = EventRegistration.objects.filter(
        user=request.user, event__is_active=True
    ).select_related('event', 'event__club').order_by('event__event_date', 'event__event_time')
    return render(request, 'my_registered_events.html', {
        'active_page': 'events',
        'page_title': 'My Registered Events',
        'registrations': registrations,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_clubs(request):
    clubs = Club.objects.all().order_by('name')
    return render(request, 'admin_portal/club_list.html', {'active_page': 'clubs', 'page_title': 'Clubs', 'clubs': clubs})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_club_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Club.objects.create(
            name=name,
            description=request.POST.get('description', ''),
            category=request.POST.get('category'),
            president=request.POST.get('president', ''),
            contact_email=request.POST.get('contact_email', ''),
            logo=request.FILES.get('logo'),
            is_active=request.POST.get('is_active') == 'on'
        )
        messages.success(request, f'Club "{name}" added successfully!')
        return redirect('admin_clubs')
    return render(request, 'admin_portal/club_add.html', {'active_page': 'clubs', 'page_title': 'Add Club'})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_club_edit(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    if request.method == 'POST':
        club.name = request.POST.get('name')
        club.description = request.POST.get('description', '')
        club.category = request.POST.get('category')
        club.president = request.POST.get('president', '')
        club.contact_email = request.POST.get('contact_email', '')
        club.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('logo'):
            club.logo = request.FILES.get('logo')
        club.save()
        msg = f'Club "{club.name}" updated successfully!'
        messages.success(request, msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg})
        return redirect('admin_clubs')
    return render(request, 'admin_portal/club_edit.html', {'active_page': 'clubs', 'page_title': 'Edit Club', 'club': club})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_club_delete(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    club_name = club.name
    club.delete()
    msg = f'Club "{club_name}" deleted successfully!'
    messages.success(request, msg)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    return redirect('admin_clubs')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_events(request):
    all_events = Event.objects.select_related('club').all().order_by('event_date', 'event_time')
    return render(request, 'admin_portal/event_list.html', {'active_page': 'events', 'page_title': 'Events', 'events': all_events})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_event_add(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        club = get_object_or_404(Club, id=request.POST.get('club'))
        Event.objects.create(
            title=title,
            description=request.POST.get('description', ''),
            club=club,
            event_date=request.POST.get('event_date'),
            event_time=request.POST.get('event_time'),
            location=request.POST.get('location'),
            image=request.FILES.get('image'),
            is_active=request.POST.get('is_active') == 'on'
        )
        messages.success(request, f'Event "{title}" added successfully!')
        return redirect('admin_events')
    clubs = Club.objects.filter(is_active=True).order_by('name')
    return render(request, 'admin_portal/event_add.html', {'active_page': 'events', 'page_title': 'Add Event', 'clubs': clubs})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.title = request.POST.get('title')
        event.description = request.POST.get('description', '')
        event.club_id = request.POST.get('club')
        event.event_date = request.POST.get('event_date')
        event.event_time = request.POST.get('event_time')
        event.location = request.POST.get('location')
        event.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('image'):
            event.image = request.FILES.get('image')
        event.save()
        msg = f'Event "{event.title}" updated successfully!'
        messages.success(request, msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg})
        return redirect('admin_events')
    clubs = Club.objects.filter(Q(is_active=True) | Q(id=event.club_id)).distinct().order_by('name')
    return render(request, 'admin_portal/event_edit.html', {'active_page': 'events', 'page_title': 'Edit Event', 'event': event, 'clubs': clubs})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event_title = event.title
    event.delete()
    msg = f'Event "{event_title}" deleted successfully!'
    messages.success(request, msg)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    return redirect('admin_events')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_event_registrations(request, event_id):
    event = get_object_or_404(Event.objects.select_related('club'), id=event_id)
    registrations = EventRegistration.objects.filter(event=event).select_related('user').order_by('-registered_at')
    return render(request, 'admin_portal/event_registrations.html', {
        'active_page': 'events',
        'page_title': f'Registrations - {event.title}',
        'event': event,
        'registrations': registrations,
    })
