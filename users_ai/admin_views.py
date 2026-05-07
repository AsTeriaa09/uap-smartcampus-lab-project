from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone

from cafeteria.models import MenuItem, Order
from transportation.models import BusRoute
from events.models import Club, Event


def admin_login(request):
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
    logout(request)
    return redirect('admin_login')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_dashboard(request):
    today = timezone.now().date()
    context = {
        'active_page': 'dashboard',
        'page_title': 'Dashboard',
        'total_menu_items': MenuItem.objects.count(),
        'available_menu_items': MenuItem.objects.filter(is_available=True).count(),
        'total_bus_routes': BusRoute.objects.count(),
        'active_bus_routes': BusRoute.objects.filter(is_active=True).count(),
        'total_clubs': Club.objects.count(),
        'active_clubs': Club.objects.filter(is_active=True).count(),
        'total_events': Event.objects.count(),
        'upcoming_events': Event.objects.filter(is_active=True, event_date__gte=today).count(),
        'total_orders': Order.objects.count(),
        'confirmed_orders': Order.objects.filter(status='confirmed').count(),
        'completed_orders': Order.objects.filter(status='completed').count(),
    }
    return render(request, 'admin_portal/dashboard.html', context)
