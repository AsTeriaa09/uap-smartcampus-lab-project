import os
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from .models import Todo
from cafeteria.models import MenuItem, Order
from transportation.models import BusRoute
from events.models import Club, Event, EventRegistration


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
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if not username or not password:
            messages.error(request, 'Username and password are required')
            return render(request, 'register.html')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'register.html')
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
    today = timezone.now().date()

    registered_events = EventRegistration.objects.filter(
        user=request.user,
        event__is_active=True,
        event__event_date__gte=today
    ).select_related('event', 'event__club').order_by('event__event_date', 'event__event_time')[:5]

    menu_count = MenuItem.objects.filter(is_available=True).count()
    events_today_count = Event.objects.filter(is_active=True, event_date=today).count()
    todos = Todo.objects.filter(user=request.user)

    return render(request, 'dashboard.html', {
        'active_page': 'dashboard',
        'page_title': 'Dashboard',
        'registered_events': registered_events,
        'menu_count': menu_count,
        'events_today_count': events_today_count,
        'todos': todos,
    })


@login_required
def ai(request):
    return render(request, 'ai.html', {
        'active_page': 'ai',
        'page_title': 'SmartCampus AI'
    })


@csrf_exempt
def ai_chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    try:
        data = json.loads(request.body)
        user_input = data.get('input', '').strip()
        if not user_input:
            return JsonResponse({'error': 'Missing or invalid input in request body.'}, status=400)
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            return JsonResponse({'error': 'Groq API key not configured.'}, status=500)

        menu_items = list(MenuItem.objects.filter(is_available=True).values('name', 'description', 'price', 'category'))[:5]
        for item in menu_items:
            if 'price' in item and hasattr(item['price'], 'quantize'):
                item['price'] = float(item['price'])

        bus_routes = list(BusRoute.objects.filter(is_active=True).values('route_name', 'departure_point', 'destination', 'departure_time', 'arrival_time', 'status'))[:3]
        for route in bus_routes:
            if 'departure_time' in route and hasattr(route['departure_time'], 'strftime'):
                route['departure_time'] = route['departure_time'].strftime('%H:%M')
            if 'arrival_time' in route and hasattr(route['arrival_time'], 'strftime'):
                route['arrival_time'] = route['arrival_time'].strftime('%H:%M')

        clubs = list(Club.objects.filter(is_active=True).values('name', 'description', 'category', 'president'))[:3]
        events = list(Event.objects.filter(is_active=True).values('title', 'description', 'event_date', 'event_time', 'location'))[:3]
        for event in events:
            if 'event_date' in event and hasattr(event['event_date'], 'isoformat'):
                event['event_date'] = event['event_date'].isoformat()
            if 'event_time' in event and hasattr(event['event_time'], 'strftime'):
                event['event_time'] = event['event_time'].strftime('%H:%M:%S')

        if request.user.is_authenticated:
            user_registered_events = list(EventRegistration.objects.filter(
                user=request.user,
                event__is_active=True
            ).select_related('event').values(
                'event__title', 'event__description', 'event__event_date', 'event__event_time'
            ))
            for ev in user_registered_events:
                if ev.get('event__event_date') is not None:
                    ev['event__event_date'] = str(ev['event__event_date'])
                if ev.get('event__event_time') is not None:
                    ev['event__event_time'] = str(ev['event__event_time'])
        else:
            user_registered_events = []

        system_prompt = f"""
You are an AI assistant for UAP SmartCampus, answering questions about campus services.

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

- Be concise and direct in your answers
- Use only the information provided above
- If you don't know the answer, say so honestly
- Focus on helping students navigate campus services
- Keep responses professional and friendly
"""
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
            return JsonResponse({'error': 'Failed to get response from AI service.'}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body.'}, status=400)
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Request timeout. Please try again.'}, status=504)
    except requests.exceptions.RequestException:
        return JsonResponse({'error': 'Failed to connect to AI service.'}, status=500)
    except Exception:
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)


@login_required
def todo_add(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    todo_type = request.POST.get('todo_type', 'assignment')
    due_date = request.POST.get('due_date') or None
    if not title:
        return JsonResponse({'success': False, 'message': 'Title is required'})
    todo = Todo.objects.create(
        user=request.user,
        title=title,
        description=description,
        todo_type=todo_type,
        due_date=due_date
    )
    from datetime import date
    due_display = None
    if todo.due_date:
        if isinstance(todo.due_date, str):
            due_display = date.fromisoformat(todo.due_date).strftime('%b %d')
        else:
            due_display = todo.due_date.strftime('%b %d')
    return JsonResponse({
        'success': True,
        'todo': {
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'todo_type': todo.todo_type,
            'due_date': due_display,
        }
    })


@login_required
def todo_edit(request, todo_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'success': False, 'message': 'Title is required'})
    todo.title = title
    todo.description = request.POST.get('description', '').strip()
    todo.todo_type = request.POST.get('todo_type', todo.todo_type)
    todo.due_date = request.POST.get('due_date') or None
    todo.save()
    from datetime import date
    due_display = None
    if todo.due_date:
        if isinstance(todo.due_date, str):
            due_display = date.fromisoformat(todo.due_date).strftime('%b %d')
        else:
            due_display = todo.due_date.strftime('%b %d')
    return JsonResponse({
        'success': True,
        'todo': {
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'todo_type': todo.todo_type,
            'due_date': due_display,
        }
    })


@login_required
def todo_delete(request, todo_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)
    todo.delete()
    return JsonResponse({'success': True})


@login_required
def todo_toggle(request, todo_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    todo = get_object_or_404(Todo, id=todo_id, user=request.user)
    todo.is_completed = not todo.is_completed
    todo.save()
    return JsonResponse({'success': True, 'is_completed': todo.is_completed})
