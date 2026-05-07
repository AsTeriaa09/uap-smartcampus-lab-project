import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder

from .models import BusRoute


@login_required
def transportation(request):
    bus_routes = BusRoute.objects.filter(is_active=True).order_by('departure_time')
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
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_bus_routes(request):
    bus_routes = BusRoute.objects.all().order_by('departure_time')
    return render(request, 'admin_portal/bus_list.html', {
        'active_page': 'bus',
        'page_title': 'Bus Routes',
        'bus_routes': bus_routes
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_bus_add(request):
    if request.method == 'POST':
        route_name = request.POST.get('route_name')
        BusRoute.objects.create(
            route_name=route_name,
            departure_point=request.POST.get('departure_point'),
            destination=request.POST.get('destination'),
            departure_time=request.POST.get('departure_time'),
            arrival_time=request.POST.get('arrival_time'),
            status=request.POST.get('status'),
            description=request.POST.get('description', ''),
            is_active=request.POST.get('is_active') == 'on'
        )
        messages.success(request, f'Bus route "{route_name}" added successfully!')
        return redirect('admin_bus_routes')
    return render(request, 'admin_portal/bus_add.html', {'active_page': 'bus', 'page_title': 'Add Bus Route'})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_bus_edit(request, route_id):
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
    return render(request, 'admin_portal/bus_edit.html', {'active_page': 'bus', 'page_title': 'Edit Bus Route', 'route': route})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_bus_delete(request, route_id):
    route = get_object_or_404(BusRoute, id=route_id)
    route_name = route.route_name
    route.delete()
    msg = f'Bus route "{route_name}" deleted successfully!'
    messages.success(request, msg)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    return redirect('admin_bus_routes')
