from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import MenuItem, BusRoute, Club, Event
from django.contrib.auth.models import User
from django.db.models import Count


# Helper function to check if user is admin/staff
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')


def user_register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation
        if not username or not password:
            messages.error(request, 'Username and password are required')
            return render(request, 'register.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'register.html')
        
        # Create user
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('dashboard')
    
    return render(request, 'register.html')


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def homepage(request):
    return render(request, 'home.html')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {
        'active_page': 'dashboard',
        'page_title': 'Dashboard'
    })


@login_required
def cafeteria(request):
    menu_items = MenuItem.objects.filter(is_available=True)
    return render(request, 'cafeteria.html', {
        'active_page': 'cafeteria',
        'page_title': 'Cafeteria',
        'menu_items': menu_items
    })


@login_required
def transportation(request):
    from django.core.serializers.json import DjangoJSONEncoder
    import json
    
    bus_routes = BusRoute.objects.filter(is_active=True).order_by('departure_time')
    
    # Prepare bus routes data for JavaScript
    bus_routes_data = []
    for route in bus_routes:
        bus_routes_data.append({
            'id': route.id,
            'route_name': route.route_name,
            'departure_point': route.departure_point,
            'destination': route.destination,
            'departure_time': route.departure_time.strftime('%H:%M'),
            'arrival_time': route.arrival_time.strftime('%H:%M'),
            'status': route.status,
            'status_display': route.get_status_display(),
            'description': route.description,
        })
    
    return render(request, 'transportation.html', {
        'active_page': 'transportation',
        'page_title': 'Transportation',
        'bus_routes': bus_routes,
        'bus_routes_json': json.dumps(bus_routes_data, cls=DjangoJSONEncoder),
    })


@login_required
def events(request):
    from django.core.serializers.json import DjangoJSONEncoder
    import json
    
    clubs = Club.objects.filter(is_active=True)
    all_events = Event.objects.filter(is_active=True).order_by('event_date', 'event_time')
    
    # Prepare clubs data for JavaScript
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
    
    # Prepare events data for JavaScript
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
        })
    
    return render(request, 'events.html', {
        'active_page': 'events',
        'page_title': 'Events & Clubs',
        'clubs': clubs,
        'events': all_events,
        'clubs_json': json.dumps(clubs_data, cls=DjangoJSONEncoder),
        'events_json': json.dumps(events_data, cls=DjangoJSONEncoder),
    })


@login_required
def ai(request):
    return render(request, 'ai.html', {
        'active_page': 'ai',
        'page_title': 'SmartCampus AI'
    })


# ==========================================
# Authority Management Portal Views
# ==========================================

def authority_login(request):
    """Login page for Authority Management Portal"""
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('authority_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if is_admin(user):
                login(request, user)
                return redirect('authority_dashboard')
            else:
                messages.error(request, 'You do not have admin privileges')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'authority/login.html')


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_logout(request):
    """Logout from Authority Management Portal"""
    logout(request)
    return redirect('authority_login')


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_dashboard(request):
    """Dashboard for Authority Management Portal"""
    total_items = MenuItem.objects.count()
    available_items = MenuItem.objects.filter(is_available=True).count()
    categories = MenuItem.objects.values('category').annotate(count=Count('id'))
    
    context = {
        'total_items': total_items,
        'available_items': available_items,
        'categories': categories,
    }
    return render(request, 'authority/dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_menu_list(request):
    """List all menu items"""
    menu_items = MenuItem.objects.all().order_by('-created_at')
    return render(request, 'authority/menu_list.html', {'menu_items': menu_items})


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_menu_add(request):
    """Add new menu item"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        category = request.POST.get('category')
        is_available = request.POST.get('is_available') == 'on'
        image = request.FILES.get('image')
        
        MenuItem.objects.create(
            name=name,
            description=description,
            price=price,
            category=category,
            is_available=is_available,
            image=image
        )
        messages.success(request, f'Menu item "{name}" added successfully!')
        return redirect('authority_menu_list')
    
    return render(request, 'authority/menu_add.html')


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_menu_edit(request, item_id):
    """Edit menu item"""
    item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.description = request.POST.get('description', '')
        item.price = request.POST.get('price')
        item.category = request.POST.get('category')
        item.is_available = request.POST.get('is_available') == 'on'
        
        if request.FILES.get('image'):
            item.image = request.FILES.get('image')
        
        item.save()
        messages.success(request, f'Menu item "{item.name}" updated successfully!')
        return redirect('authority_menu_list')
    
    return render(request, 'authority/menu_edit.html', {'item': item})


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_menu_delete(request, item_id):
    """Delete menu item"""
    item = get_object_or_404(MenuItem, id=item_id)
    item_name = item.name
    item.delete()
    messages.success(request, f'Menu item "{item_name}" deleted successfully!')
    return redirect('authority_menu_list')


# ==========================================
# UAP Admin Portal Views (/uapadmin)
# ==========================================

def admin_login(request):
    """Login page for UAP Admin Portal - Superuser only"""
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Access denied. Superuser privileges required.')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'admin_portal/login.html')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_logout(request):
    """Logout from UAP Admin Portal"""
    logout(request)
    return redirect('admin_login')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_dashboard(request):
    """Dashboard for UAP Admin Portal"""
    total_menu_items = MenuItem.objects.count()
    available_menu_items = MenuItem.objects.filter(is_available=True).count()
    total_bus_routes = BusRoute.objects.count()
    active_bus_routes = BusRoute.objects.filter(is_active=True).count()
    total_clubs = Club.objects.count()
    active_clubs = Club.objects.filter(is_active=True).count()
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(is_active=True, event_date__gte='2026-04-24').count()
    
    context = {
        'active_page': 'dashboard',
        'page_title': 'Dashboard',
        'total_menu_items': total_menu_items,
        'available_menu_items': available_menu_items,
        'total_bus_routes': total_bus_routes,
        'active_bus_routes': active_bus_routes,
        'total_clubs': total_clubs,
        'active_clubs': active_clubs,
        'total_events': total_events,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'admin_portal/dashboard.html', context)


# Menu Management
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_menu_list(request):
    """List all menu items"""
    menu_items = MenuItem.objects.all().order_by('-created_at')
    return render(request, 'admin_portal/menu_list.html', {
        'active_page': 'menu',
        'page_title': 'Cafeteria Menu',
        'menu_items': menu_items
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_menu_add(request):
    """Add new menu item"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        category = request.POST.get('category')
        is_available = request.POST.get('is_available') == 'on'
        image = request.FILES.get('image')
        
        MenuItem.objects.create(
            name=name,
            description=description,
            price=price,
            category=category,
            is_available=is_available,
            image=image
        )
        messages.success(request, f'Menu item "{name}" added successfully!')
        return redirect('admin_menu_list')
    
    return render(request, 'admin_portal/menu_add.html', {
        'active_page': 'menu',
        'page_title': 'Add Menu Item'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_menu_edit(request, item_id):
    """Edit menu item"""
    item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.description = request.POST.get('description', '')
        item.price = request.POST.get('price')
        item.category = request.POST.get('category')
        item.is_available = request.POST.get('is_available') == 'on'
        
        if request.FILES.get('image'):
            item.image = request.FILES.get('image')
        
        item.save()
        msg = f'Menu item "{item.name}" updated successfully!'
        messages.success(request, msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg})
        return redirect('admin_menu_list')
    
    return render(request, 'admin_portal/menu_edit.html', {
        'active_page': 'menu',
        'page_title': 'Edit Menu Item',
        'item': item
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_menu_delete(request, item_id):
    """Delete menu item"""
    item = get_object_or_404(MenuItem, id=item_id)
    item_name = item.name
    item.delete()
    msg = f'Menu item "{item_name}" deleted successfully!'
    messages.success(request, msg)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    return redirect('admin_menu_list')


# Bus Route Management
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_bus_routes(request):
    """List all bus routes"""
    bus_routes = BusRoute.objects.all().order_by('departure_time')
    return render(request, 'admin_portal/bus_list.html', {
        'active_page': 'bus',
        'page_title': 'Bus Routes',
        'bus_routes': bus_routes
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_bus_add(request):
    """Add new bus route"""
    if request.method == 'POST':
        route_name = request.POST.get('route_name')
        departure_point = request.POST.get('departure_point')
        destination = request.POST.get('destination')
        departure_time = request.POST.get('departure_time')
        arrival_time = request.POST.get('arrival_time')
        status = request.POST.get('status')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        BusRoute.objects.create(
            route_name=route_name,
            departure_point=departure_point,
            destination=destination,
            departure_time=departure_time,
            arrival_time=arrival_time,
            status=status,
            description=description,
            is_active=is_active
        )
        messages.success(request, f'Bus route "{route_name}" added successfully!')
        return redirect('admin_bus_routes')
    
    return render(request, 'admin_portal/bus_add.html', {
        'active_page': 'bus',
        'page_title': 'Add Bus Route'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_bus_edit(request, route_id):
    """Edit bus route"""
    route = get_object_or_404(BusRoute, id=route_id)
    
    if request.method == 'POST':
        route.route_name = request.POST.get('route_name')
        route.departure_point = request.POST.get('departure_point')
        route.destination = request.POST.get('destination')
        route.departure_time = request.POST.get('departure_time')
        route.arrival_time = request.POST.get('arrival_time')
        route.status = request.POST.get('status')
        route.description = request.POST.get('description', '')
        route.is_active = request.POST.get('is_active') == 'on'
        
        route.save()
        msg = f'Bus route "{route.route_name}" updated successfully!'
        messages.success(request, msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg})
        return redirect('admin_bus_routes')
    
    return render(request, 'admin_portal/bus_edit.html', {
        'active_page': 'bus',
        'page_title': 'Edit Bus Route',
        'route': route
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_bus_delete(request, route_id):
    """Delete bus route"""
    route = get_object_or_404(BusRoute, id=route_id)
    route_name = route.route_name
    route.delete()
    msg = f'Bus route "{route_name}" deleted successfully!'
    messages.success(request, msg)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    return redirect('admin_bus_routes')


# Club Management
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_clubs(request):
    """List all clubs"""
    clubs = Club.objects.all().order_by('name')
    return render(request, 'admin_portal/club_list.html', {
        'active_page': 'clubs',
        'page_title': 'Clubs',
        'clubs': clubs
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_club_add(request):
    """Add new club"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        category = request.POST.get('category')
        president = request.POST.get('president', '')
        contact_email = request.POST.get('contact_email', '')
        logo = request.FILES.get('logo')
        is_active = request.POST.get('is_active') == 'on'
        
        Club.objects.create(
            name=name,
            description=description,
            category=category,
            president=president,
            contact_email=contact_email,
            logo=logo,
            is_active=is_active
        )
        messages.success(request, f'Club "{name}" added successfully!')
        return redirect('admin_clubs')
    
    return render(request, 'admin_portal/club_add.html', {
        'active_page': 'clubs',
        'page_title': 'Add Club'
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_club_edit(request, club_id):
    """Edit club"""
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
    
    return render(request, 'admin_portal/club_edit.html', {
        'active_page': 'clubs',
        'page_title': 'Edit Club',
        'club': club
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_club_delete(request, club_id):
    """Delete club"""
    club = get_object_or_404(Club, id=club_id)
    club_name = club.name
    club.delete()
    msg = f'Club "{club_name}" deleted successfully!'
    messages.success(request, msg)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    return redirect('admin_clubs')


# Event Management
@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_events(request):
    """List all events"""
    events = Event.objects.select_related('club').all().order_by('event_date', 'event_time')
    return render(request, 'admin_portal/event_list.html', {
        'active_page': 'events',
        'page_title': 'Events',
        'events': events
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_event_add(request):
    """Add new event"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        club_id = request.POST.get('club')
        event_date = request.POST.get('event_date')
        event_time = request.POST.get('event_time')
        location = request.POST.get('location')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'
        
        club = get_object_or_404(Club, id=club_id)
        
        Event.objects.create(
            title=title,
            description=description,
            club=club,
            event_date=event_date,
            event_time=event_time,
            location=location,
            image=image,
            is_active=is_active
        )
        messages.success(request, f'Event "{title}" added successfully!')
        return redirect('admin_events')
    
    clubs = Club.objects.filter(is_active=True)
    return render(request, 'admin_portal/event_add.html', {
        'active_page': 'events',
        'page_title': 'Add Event',
        'clubs': clubs
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_event_edit(request, event_id):
    """Edit event"""
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
    
    clubs = Club.objects.filter(is_active=True)
    return render(request, 'admin_portal/event_edit.html', {
        'active_page': 'events',
        'page_title': 'Edit Event',
        'event': event,
        'clubs': clubs
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_event_delete(request, event_id):
    """Delete event"""
    event = get_object_or_404(Event, id=event_id)
    event_title = event.title
    event.delete()
    msg = f'Event "{event_title}" deleted successfully!'
    messages.success(request, msg)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    return redirect('admin_events')
