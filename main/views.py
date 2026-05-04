import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .models import MenuItem, BusRoute, Club, Event, Order, OrderItem, EventRegistration
from django.contrib.auth.models import User
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import requests


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
    from django.utils import timezone
    registered_events = EventRegistration.objects.filter(
        user=request.user,
        event__is_active=True,
        event__event_date__gte=timezone.now().date()
    ).select_related('event', 'event__club').order_by('event__event_date', 'event__event_time')[:5]
    
    return render(request, 'dashboard.html', {
        'active_page': 'dashboard',
        'page_title': 'Dashboard',
        'registered_events': registered_events,
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
    from django.utils import timezone
    
    clubs = Club.objects.filter(is_active=True)
    all_events = Event.objects.filter(is_active=True).order_by('event_date', 'event_time')
    
    # Get user's registered event IDs
    user_registered_event_ids = set(
        EventRegistration.objects.filter(user=request.user)
        .values_list('event_id', flat=True)
    )
    
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
    """Register user for an event via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    event = get_object_or_404(Event, id=event_id, is_active=True)
    
    # Check if already registered
    if EventRegistration.objects.filter(user=request.user, event=event).exists():
        return JsonResponse({
            'success': False,
            'message': 'You are already registered for this event',
            'is_registered': True,
            'registration_count': event.registration_count
        })
    
    # Get registration details from request
    full_name = request.POST.get('full_name', '').strip()
    registration_number = request.POST.get('registration_number', '').strip()
    edu_email = request.POST.get('edu_email', '').strip()
    department = request.POST.get('department', '').strip()
    
    # Validate required fields
    if not full_name:
        return JsonResponse({'success': False, 'message': 'Full name is required'})
    if not registration_number:
        return JsonResponse({'success': False, 'message': 'Registration number is required'})
    if not edu_email:
        return JsonResponse({'success': False, 'message': 'Educational email is required'})
    if not department:
        return JsonResponse({'success': False, 'message': 'Department is required'})
    
    EventRegistration.objects.create(
        user=request.user,
        event=event,
        full_name=full_name,
        registration_number=registration_number,
        edu_email=edu_email,
        department=department
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Successfully registered for "{event.title}"',
        'is_registered': True,
        'registration_count': event.registration_count
    })


@login_required
def unregister_from_event(request, event_id):
    """Unregister user from an event via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    event = get_object_or_404(Event, id=event_id, is_active=True)
    
    registration = EventRegistration.objects.filter(user=request.user, event=event).first()
    if not registration:
        return JsonResponse({
            'success': False,
            'message': 'You are not registered for this event',
            'is_registered': False,
            'registration_count': event.registration_count
        })
    
    registration.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Successfully unregistered from "{event.title}"',
        'is_registered': False,
        'registration_count': event.registration_count
    })


@login_required
def my_registered_events(request):
    """Display user's registered events"""
    registrations = EventRegistration.objects.filter(
        user=request.user,
        event__is_active=True
    ).select_related('event', 'event__club').order_by('event__event_date', 'event__event_time')
    
    return render(request, 'my_registered_events.html', {
        'active_page': 'events',
        'page_title': 'My Registered Events',
        'registrations': registrations,
    })


@login_required
def ai(request):
    return render(request, 'ai.html', {
        'active_page': 'ai',
        'page_title': 'SmartCampus AI'
    })


@csrf_exempt
def ai_chat_api(request):
    """
    Django view to handle AI chat requests using Groq API
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        # Parse JSON data
        data = json.loads(request.body)
        user_input = data.get('input', '').strip()
        
        # Validate input
        if not user_input:
            return JsonResponse({'error': 'Missing or invalid input in request body.'}, status=400)
        
        # Get Groq API key from environment
        groq_api_key = os.getenv('GROQ_API_KEY')
        print(f'GROQ_API_KEY loaded: {groq_api_key is not None}')
        if not groq_api_key:
            return JsonResponse({'error': 'Groq API key not configured.'}, status=500)
        
        # Fetch campus data for context
        menu_items = list(MenuItem.objects.filter(is_available=True).values('name', 'description', 'price', 'category'))[:5]
        # Convert Decimal fields to strings for JSON serialization
        for item in menu_items:
            if 'price' in item and hasattr(item['price'], 'quantize'):
                item['price'] = float(item['price'])
        
        bus_routes = list(BusRoute.objects.filter(is_active=True).values('route_name', 'departure_point', 'destination', 'departure_time', 'arrival_time', 'status'))[:3]
        # Convert time fields to strings for JSON serialization
        for route in bus_routes:
            if 'departure_time' in route and hasattr(route['departure_time'], 'strftime'):
                route['departure_time'] = route['departure_time'].strftime('%H:%M')
            if 'arrival_time' in route and hasattr(route['arrival_time'], 'strftime'):
                route['arrival_time'] = route['arrival_time'].strftime('%H:%M')
        
        clubs = list(Club.objects.filter(is_active=True).values('name', 'description', 'category', 'president'))[:3]
        events = list(Event.objects.filter(is_active=True).values('title', 'description', 'event_date', 'event_time', 'location'))[:3]
        # Convert date/time fields to strings for JSON serialization
        for event in events:
            if 'event_date' in event and hasattr(event['event_date'], 'isoformat'):
                event['event_date'] = event['event_date'].isoformat()
            if 'event_time' in event and hasattr(event['event_time'], 'strftime'):
                event['event_time'] = event['event_time'].strftime('%H:%M:%S')
        
        # Get user-specific data (handle both authenticated and anonymous users)
        if request.user.is_authenticated:
            user_registered_events = list(EventRegistration.objects.filter(
                user=request.user,
                event__is_active=True
            ).select_related('event').values(
                'event__title', 'event__description', 'event__event_date', 'event__event_time'
            ))
        else:
            user_registered_events = []
        
        # Build system prompt with campus data
        system_prompt = f"""
You are an AI assistant for UAP SmartCampus, answering questions about campus services.

Here's verified information about UAP SmartCampus:

Menu Items (Cafeteria):
{json.dumps(menu_items, indent=2) if menu_items else 'No menu items available'}

Bus Routes (Transportation):
{json.dumps(bus_routes, indent=2) if bus_routes else 'No bus routes available'}

Clubs:
{json.dumps(clubs, indent=2) if clubs else 'No clubs available'}

Events:
{json.dumps(events, indent=2) if events else 'No events available'}

User's Registered Events:
{json.dumps(user_registered_events, indent=2) if user_registered_events else 'User has not registered for any events'}

Your task is to answer questions about campus services accurately and helpfully.
- Be concise and direct in your answers
- Use only the information provided above
- If you don't know the answer, say so honestly
- Focus on helping students navigate campus services
- Keep responses professional and friendly
"""

        # Call Groq API
        headers = {
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_input}
            ],
            'model': 'llama-3.1-8b-instant',
            'temperature': 0.7,
            'max_tokens': 500,
            'top_p': 0.8
        }
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            return JsonResponse({'answer': ai_response})
        else:
            error_msg = f'Groq API error: {response.status_code} - {response.text}'
            print(error_msg)
            return JsonResponse({'error': 'Failed to get response from AI service.'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Request timeout. Please try again.'}, status=504)
    except requests.exceptions.RequestException as e:
        print(f'Groq API request error: {e}')
        return JsonResponse({'error': 'Failed to connect to AI service.'}, status=500)
    except Exception as e:
        print(f'Unexpected error in AI chat API: {e}')
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)


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
    total_orders = Order.objects.count()
    confirmed_orders = Order.objects.filter(status='confirmed').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
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
        'total_orders': total_orders,
        'confirmed_orders': confirmed_orders,
        'completed_orders': completed_orders,
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
def admin_event_registrations(request, event_id):
    """View all registrations for a specific event"""
    event = get_object_or_404(Event.objects.select_related('club'), id=event_id)
    registrations = EventRegistration.objects.filter(
        event=event
    ).select_related('user').order_by('-registered_at')
    
    return render(request, 'admin_portal/event_registrations.html', {
        'active_page': 'events',
        'page_title': f'Registrations - {event.title}',
        'event': event,
        'registrations': registrations,
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
    
    clubs = Club.objects.filter(is_active=True).order_by('name')
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
    
    clubs = Club.objects.filter(Q(is_active=True) | Q(id=event.club_id)).distinct().order_by('name')
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


# ==========================================
# User Cart & Order Views
# ==========================================

@login_required
def add_to_cart(request, item_id):
    """Add item to session cart via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    quantity = int(request.POST.get('quantity', 1))
    
    cart = request.session.get('cart', {})
    cart[str(item_id)] = cart.get(str(item_id), 0) + quantity
    request.session['cart'] = cart
    request.session.modified = True
    
    cart_count = sum(cart.values())
    return JsonResponse({'success': True, 'message': f'Added {item.name} to cart', 'cart_count': cart_count})


@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    quantity = int(request.POST.get('quantity', 1))
    cart = request.session.get('cart', {})
    
    if str(item_id) in cart:
        if quantity > 0:
            cart[str(item_id)] = quantity
        else:
            del cart[str(item_id)]
        request.session['cart'] = cart
        request.session.modified = True
    
    cart_count = sum(cart.values())
    return JsonResponse({'success': True, 'cart_count': cart_count})


@login_required
def remove_from_cart(request, item_id):
    """Remove item from session cart via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    cart = request.session.get('cart', {})
    if str(item_id) in cart:
        del cart[str(item_id)]
        request.session['cart'] = cart
        request.session.modified = True
    
    cart_count = sum(cart.values())
    return JsonResponse({'success': True, 'message': 'Item removed from cart', 'cart_count': cart_count})


@login_required
def cart_view(request):
    """Display cart page"""
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
    for item_id, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=int(item_id), is_available=True)
            subtotal = item.price * quantity
            total += subtotal
            cart_items.append({
                'item': item,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except MenuItem.DoesNotExist:
            continue
    
    return render(request, 'cart.html', {
        'active_page': 'cafeteria',
        'page_title': 'My Cart',
        'cart_items': cart_items,
        'total': total,
    })


@login_required
def confirm_order(request):
    """Confirm order from session cart"""
    if request.method != 'POST':
        return redirect('cart_view')
    
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty')
        return redirect('cart_view')
    
    order = Order.objects.create(user=request.user, status='confirmed', total_amount=0)
    total = 0
    
    for item_id, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=int(item_id), is_available=True)
            subtotal = item.price * quantity
            total += subtotal
            OrderItem.objects.create(
                order=order,
                menu_item=item,
                quantity=quantity,
                price_at_time=item.price
            )
        except MenuItem.DoesNotExist:
            continue
    
    order.total_amount = total
    order.save()
    
    request.session['cart'] = {}
    request.session.modified = True
    
    messages.success(request, f'Order #{order.id} placed successfully!')
    return redirect('my_orders')


@login_required
def order_now(request, item_id):
    """Order a single item immediately (bypass cart)"""
    if request.method != 'POST':
        return redirect('cafeteria')
    
    try:
        item = MenuItem.objects.get(id=item_id, is_available=True)
    except MenuItem.DoesNotExist:
        messages.error(request, 'Item not found or unavailable')
        return redirect('cafeteria')
    
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1
    if quantity > 10:
        quantity = 10
    
    order = Order.objects.create(
        user=request.user,
        status='confirmed',
        total_amount=item.price * quantity
    )
    OrderItem.objects.create(
        order=order,
        menu_item=item,
        quantity=quantity,
        price_at_time=item.price
    )
    
    messages.success(request, f'Order #{order.id} for {item.name} placed successfully!')
    return redirect('my_orders')


@login_required
def my_orders(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__menu_item').order_by('-created_at')
    return render(request, 'my_orders.html', {
        'active_page': 'cafeteria',
        'page_title': 'My Orders',
        'orders': orders,
    })


# ==========================================
# Admin Order Management Views
# ==========================================

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_orders(request):
    """List all orders in admin portal"""
    status_filter = request.GET.get('status', '')
    orders = Order.objects.select_related('user').prefetch_related('items__menu_item').order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    status_counts = {
        'all': Order.objects.count(),
        'confirmed': Order.objects.filter(status='confirmed').count(),
        'completed': Order.objects.filter(status='completed').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    return render(request, 'admin_portal/order_list.html', {
        'active_page': 'orders',
        'page_title': 'Orders',
        'orders': orders,
        'status_filter': status_filter,
        'status_counts': status_counts,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_order_detail(request, order_id):
    """View order details in admin portal"""
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('items__menu_item'), id=order_id)
    return render(request, 'admin_portal/order_detail.html', {
        'active_page': 'orders',
        'page_title': f'Order #{order.id}',
        'order': order,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_order_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            msg = f'Order #{order.id} status updated to {order.get_status_display()}'
            messages.success(request, msg)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': msg})
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('admin_order_detail', order_id=order.id)
