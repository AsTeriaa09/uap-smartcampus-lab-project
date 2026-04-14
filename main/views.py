from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import MenuItem
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
    return render(request, 'transportation.html', {
        'active_page': 'transportation',
        'page_title': 'Transportation'
    })


@login_required
def events(request):
    return render(request, 'events.html', {
        'active_page': 'events',
        'page_title': 'Events & Clubs'
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
