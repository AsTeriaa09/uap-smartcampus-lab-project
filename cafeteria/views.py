import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count

from .models import MenuItem, Order, OrderItem


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
def cafeteria(request):
    menu_items = MenuItem.objects.filter(is_available=True)
    return render(request, 'cafeteria.html', {
        'active_page': 'cafeteria',
        'page_title': 'Cafeteria',
        'menu_items': menu_items
    })


@login_required
def add_to_cart(request, item_id):
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
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for item_id, quantity in cart.items():
        try:
            item = MenuItem.objects.get(id=int(item_id), is_available=True)
            subtotal = item.price * quantity
            total += subtotal
            cart_items.append({'item': item, 'quantity': quantity, 'subtotal': subtotal})
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
            OrderItem.objects.create(order=order, menu_item=item, quantity=quantity, price_at_time=item.price)
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
    if request.method != 'POST':
        return redirect('cafeteria')
    try:
        item = MenuItem.objects.get(id=item_id, is_available=True)
    except MenuItem.DoesNotExist:
        messages.error(request, 'Item not found or unavailable')
        return redirect('cafeteria')
    quantity = int(request.POST.get('quantity', 1))
    quantity = max(1, min(10, quantity))
    order = Order.objects.create(user=request.user, status='confirmed', total_amount=item.price * quantity)
    OrderItem.objects.create(order=order, menu_item=item, quantity=quantity, price_at_time=item.price)
    messages.success(request, f'Order #{order.id} for {item.name} placed successfully!')
    return redirect('my_orders')


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__menu_item').order_by('-created_at')
    return render(request, 'my_orders.html', {
        'active_page': 'cafeteria',
        'page_title': 'My Orders',
        'orders': orders,
    })


def authority_login(request):
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
    logout(request)
    return redirect('authority_login')


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_dashboard(request):
    total_items = MenuItem.objects.count()
    available_items = MenuItem.objects.filter(is_available=True).count()
    categories = MenuItem.objects.values('category').annotate(count=Count('id'))
    return render(request, 'authority/dashboard.html', {
        'total_items': total_items,
        'available_items': available_items,
        'categories': categories,
    })


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_menu_list(request):
    menu_items = MenuItem.objects.all().order_by('-created_at')
    return render(request, 'authority/menu_list.html', {'menu_items': menu_items})


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_menu_add(request):
    if request.method == 'POST':
        MenuItem.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            price=request.POST.get('price'),
            category=request.POST.get('category'),
            is_available=request.POST.get('is_available') == 'on',
            image=request.FILES.get('image')
        )
        messages.success(request, f'Menu item added successfully!')
        return redirect('authority_menu_list')
    return render(request, 'authority/menu_add.html')


@login_required
@user_passes_test(is_admin, login_url='/authority/login/')
def authority_menu_edit(request, item_id):
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
    item = get_object_or_404(MenuItem, id=item_id)
    item.delete()
    messages.success(request, f'Menu item deleted successfully!')
    return redirect('authority_menu_list')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_menu_list(request):
    menu_items = MenuItem.objects.all().order_by('-created_at')
    return render(request, 'admin_portal/menu_list.html', {
        'active_page': 'menu',
        'page_title': 'Cafeteria Menu',
        'menu_items': menu_items
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_menu_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        MenuItem.objects.create(
            name=name,
            description=request.POST.get('description', ''),
            price=request.POST.get('price'),
            category=request.POST.get('category'),
            is_available=request.POST.get('is_available') == 'on',
            image=request.FILES.get('image')
        )
        messages.success(request, f'Menu item "{name}" added successfully!')
        return redirect('admin_menu_list')
    return render(request, 'admin_portal/menu_add.html', {'active_page': 'menu', 'page_title': 'Add Menu Item'})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_menu_edit(request, item_id):
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
    return render(request, 'admin_portal/menu_edit.html', {'active_page': 'menu', 'page_title': 'Edit Menu Item', 'item': item})


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_menu_delete(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item_name = item.name
    item.delete()
    msg = f'Menu item "{item_name}" deleted successfully!'
    messages.success(request, msg)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    return redirect('admin_menu_list')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_orders(request):
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
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('items__menu_item'), id=order_id)
    return render(request, 'admin_portal/order_detail.html', {
        'active_page': 'orders',
        'page_title': f'Order #{order.id}',
        'order': order,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/uapadmin/login/')
def admin_order_status(request, order_id):
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
