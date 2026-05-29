import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.models import User
from django.db.models import Q
from django.conf import settings
from django.contrib import messages

from .models import Customer, Restaurant, Item, Cart, Order, Offer, DiningRestaurant, DiningTable, Reservation, DiningOffer

import razorpay

# ─────────────────────────────────────────────
# Helper: session-based login guard
# ─────────────────────────────────────────────
def get_logged_in_customer(request):
    """Returns the Customer object if logged in, else None."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return Customer.objects.get(id=user_id)
    except Customer.DoesNotExist:
        return None


def login_required_view(view_func):
    """Decorator: redirect to signin if not logged in."""
    def wrapper(request, *args, **kwargs):
        if not get_logged_in_customer(request):
            return redirect('open_signin')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_view(view_func):
    """Decorator: only allow if the session user is staff (Django superuser)."""
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        # We treat Django superusers as admins; simple check via session flag
        if not request.session.get('is_admin'):
            return redirect('open_signin')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# Public views
# ─────────────────────────────────────────────
def index(request):
    customer = get_logged_in_customer(request)
    if customer:
        return redirect('dashboard', username=customer.username)
    return render(request, 'delivery/index.html')


def open_signin(request):
    if get_logged_in_customer(request):
        customer = get_logged_in_customer(request)
        return redirect('dashboard', username=customer.username)
    return render(request, 'delivery/signin.html')


def open_signup(request):
    if get_logged_in_customer(request):
        customer = get_logged_in_customer(request)
        return redirect('dashboard', username=customer.username)
    return render(request, 'delivery/signup.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm  = request.POST.get('confirm_password', '')
        email    = request.POST.get('email', '').strip()
        mobile   = request.POST.get('mobile', '').strip()
        address  = request.POST.get('address', '').strip()

        print(f"\n--- SIGNUP AUDIT ---")
        print(f"Incoming: {username}, {email}")

        # Server-side password match check
        if password != confirm:
            return render(request, 'delivery/signup.html', {"error": "Passwords do not match!"})

        if len(password) < 6:
            return render(request, 'delivery/signup.html', {"error": "Password must be at least 6 characters."})

        if Customer.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).exists():
            print(f"Signup Blocked: Duplicate username or email")
            return render(request, 'delivery/signup.html', {"error": "Username or Email already exists!"})

        try:
            password_hash = make_password(password)
            Customer.objects.create(
                username=username,
                password=password_hash,
                email=email,
                mobile=mobile,
                address=address
            )
            print(f"Signup Success: {username}")
            messages.success(request, "Account created successfully! Please sign in to continue.")
            return redirect('open_signin')
        except Exception as e:
            print(f"Signup DB Error: {str(e)}")
            return render(request, 'delivery/signup.html', {"error": "Could not save user. Please try again."})

    return render(request, 'delivery/signup.html')


def signin(request):
    if request.method == 'POST':
        entered_value    = request.POST.get('username', '').strip()
        entered_password = request.POST.get('password', '')

        print(f"\n--- LOGIN AUDIT ---")
        print(f"ATTEMPT: {entered_value}")

        # 1. Try to authenticate as standard Django staff/superuser first
        django_username = entered_value
        if '@' in entered_value:
            # Resolve email to username for Django User model
            dj_user_by_email = User.objects.filter(email__iexact=entered_value).first()
            if dj_user_by_email:
                django_username = dj_user_by_email.username

        django_user = authenticate(request, username=django_username, password=entered_password)
        if django_user is not None:
            if django_user.is_staff or django_user.is_superuser:
                print(f"AUTH RESULT: DJANGO ADMIN SUCCESS")
                django_login(request, django_user)
                request.session['is_admin']   = True
                request.session['admin_name'] = django_user.username
                return JsonResponse({'success': True, 'redirect': '/admin/'})

        # 2. Try to authenticate as custom Customer
        customer = Customer.objects.filter(
            Q(username__iexact=entered_value) | Q(email__iexact=entered_value)
        ).first()

        if customer and check_password(entered_password, customer.password):
            print(f"AUTH RESULT: CUSTOMER SUCCESS")
            request.session['user_id']  = customer.id
            request.session['username'] = customer.username
            request.session.set_expiry(86400)  # 24 h session
            redirect_url = f"/signin_success/{customer.username}/"
            return JsonResponse({'success': True, 'redirect': redirect_url})
        else:
            print(f"AUTH RESULT: FAILED")
            return JsonResponse({'success': False, 'message': "Invalid username or password"}, status=401)

    return render(request, 'delivery/signin.html')


def logout(request):
    request.session.flush()
    return redirect('index')


def signin_success(request, username):
    return render(request, 'delivery/login_transition.html', {"username": username})


# ─────────────────────────────────────────────
# Customer views (login required)
# ─────────────────────────────────────────────
@login_required_view
def dashboard(request, username):
    customer = get_logged_in_customer(request)
    # Prevent accessing another user's dashboard
    if customer.username != username:
        return redirect('dashboard', username=customer.username)
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/customer_home.html', {
        "restaurantList": restaurantList,
        "username": username,
    })


@login_required_view
def view_menu(request, restaurant_id, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dashboard', username=customer.username)
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList   = restaurant.items.all()
    return render(request, 'delivery/customer_menu.html', {
        "itemList":    itemList,
        "restaurant":  restaurant,
        "username":    username,
    })


@login_required_view
def add_to_cart(request, item_id, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dashboard', username=customer.username)
    item = get_object_or_404(Item, id=item_id)
    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart.items.add(item)
    return redirect('view_menu', restaurant_id=item.restaurant.id, username=username)


@login_required_view
def remove_from_cart(request, item_id, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dashboard', username=customer.username)
    item = get_object_or_404(Item, id=item_id)
    cart = Cart.objects.filter(customer=customer).first()
    if cart:
        cart.items.remove(item)
    return redirect('show_cart', username=username)


@login_required_view
def show_cart(request, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dashboard', username=customer.username)
    cart        = Cart.objects.filter(customer=customer).first()
    items       = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0
    
    # Dynamic recommendations: Fetch items NOT in cart
    item_ids_in_cart = [item.id for item in items]
    recommended_items = Item.objects.exclude(id__in=item_ids_in_cart).order_by('?')[:8]
    
    return render(request, 'delivery/cart.html', {
        "itemList":    items,
        "total_price": total_price,
        "username":    username,
        "customer":    customer,
        "recommended_items": recommended_items,
    })


@login_required_view
def checkout(request, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dashboard', username=customer.username)

    payment_for = request.GET.get('mode', 'delivery')
    
    if payment_for == 'dining':
        pending = request.session.get('pending_reservation')
        if not pending:
            return redirect('dining_home', username=username)
            
        fee = float(pending['reservation_fee'])
        platform_fee = 50.0
        tax = (fee + platform_fee) * 0.18
        total_price = fee + platform_fee + tax
        cart_items = []
        dining_restaurant = DiningRestaurant.objects.get(id=pending['restaurant_id'])
    else:
        cart        = Cart.objects.filter(customer=customer).first()
        cart_items  = cart.items.all() if cart else []
        total_price = cart.total_price() if cart else 0
        dining_restaurant = None

    if total_price == 0:
        return render(request, 'delivery/checkout.html', {
            'error':    'Your cart is empty! Add items before checking out.',
            'username': username,
        })

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order_data = {
            'amount':          int(total_price * 100),  # paisa
            'currency':        'INR',
            'payment_capture': '1',
        }
        order = client.order.create(data=order_data)
        razorpay_order_id = order['id']
    except Exception as e:
        print(f"Razorpay Error: {e}")
        razorpay_order_id = None

    return render(request, 'delivery/checkout.html', {
        'username':          username,
        'customer':          customer,
        'cart_items':        cart_items,
        'total_price':       round(total_price, 2),
        'razorpay_key_id':   settings.RAZORPAY_KEY_ID,
        'order_id':          razorpay_order_id,
        'amount':            int(total_price * 100),
        'payment_for':       payment_for,
        'dining_restaurant': dining_restaurant,
        'pending':           pending if payment_for == 'dining' else None
    })


@login_required_view
def orders(request, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dashboard', username=customer.username)

    # If payment details are posted (Razorpay callback)
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_order_id   = request.POST.get('razorpay_order_id', '')
    discounted_total_str = request.POST.get('discounted_total', None)
    payment_for         = request.POST.get('payment_for', 'delivery')

    if payment_for == 'dining':
        import uuid
        pending = request.session.get('pending_reservation')
        if pending and razorpay_payment_id:
            restaurant = DiningRestaurant.objects.get(id=pending['restaurant_id'])
            table = DiningTable.objects.get(id=pending['table_id'])
            
            res = Reservation.objects.create(
                user=customer,
                restaurant=restaurant,
                table=table,
                booking_date=pending['date'],
                booking_time=pending['time'],
                guests=pending['guests'],
                occasion=pending['occasion'],
                special_request=pending['special_request'],
                status='confirmed',
                payment_status='paid',
                advance_amount=pending['reservation_fee'],
                transaction_id=razorpay_payment_id,
                booking_reference=str(uuid.uuid4()).split('-')[0].upper()
            )
            if 'pending_reservation' in request.session:
                del request.session['pending_reservation']
            return redirect('my_reservations', username=username)
        return redirect('dining_home', username=username)

    cart        = Cart.objects.filter(customer=customer).first()
    cart_items  = list(cart.items.all()) if cart else []
    total_price = cart.total_price() if cart else 0
    
    if discounted_total_str:
        try:
            total_price = float(discounted_total_str)
        except ValueError:
            pass

    # Persist the order
    if cart_items:
        items_data = [
            {"name": i.name, "price": i.price, "description": i.description}
            for i in cart_items
        ]
        Order.objects.create(
            customer            = customer,
            items_snapshot      = json.dumps(items_data),
            total_price         = total_price,
            address             = customer.address,
            status              = 'placed',
            razorpay_order_id   = razorpay_order_id or None,
            razorpay_payment_id = razorpay_payment_id or None,
        )
        # Clear the cart after saving the order
        if cart:
            cart.items.clear()

    steps = [
        ('placed',      'Placed',      'fas fa-check'),
        ('preparing',   'Preparing',   'fas fa-fire'),
        ('on_the_way',  'On the Way',  'fas fa-motorcycle'),
        ('delivered',   'Delivered',   'fas fa-house'),
    ]
    return render(request, 'delivery/orders.html', {
        'username':    username,
        'customer':    customer,
        'cart_items':  cart_items,
        'total_price': total_price,
        'steps':       steps,
    })


@login_required_view
def order_history(request, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dashboard', username=customer.username)
    orders_list = Order.objects.filter(customer=customer)
    return render(request, 'delivery/order_history.html', {
        'username':    username,
        'orders_list': orders_list,
    })


# ─────────────────────────────────────────────
# Admin / restaurant management views
# (protected: only accessible when is_admin flag is set in session)
# ─────────────────────────────────────────────
def _is_admin(request):
    return request.session.get('is_admin', False)


def admin_home(request):
    if not _is_admin(request):
        return redirect('open_signin')
    return render(request, 'delivery/admin_home.html')


def open_add_restaurant(request):
    if not _is_admin(request):
        return redirect('open_signin')
    return render(request, 'delivery/add_restaurant.html')


def add_restaurant(request):
    if not _is_admin(request):
        return redirect('open_signin')
    if request.method == 'POST':
        name    = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating  = request.POST.get('rating')
        if Restaurant.objects.filter(name__iexact=name).exists():
            return HttpResponse("Duplicate restaurant!")
        Restaurant.objects.create(name=name, picture=picture, cuisine=cuisine, rating=rating)
    return render(request, 'delivery/admin_home.html')


def open_show_restaurant(request):
    if not _is_admin(request):
        return redirect('open_signin')
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList})


def open_update_restaurant(request, restaurant_id):
    if not _is_admin(request):
        return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(request, 'delivery/update_restaurant.html', {"restaurant": restaurant})


def update_restaurant(request, restaurant_id):
    if not _is_admin(request):
        return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        restaurant.name    = request.POST.get('name')
        restaurant.picture = request.POST.get('picture')
        restaurant.cuisine = request.POST.get('cuisine')
        restaurant.rating  = request.POST.get('rating')
        restaurant.save()
    return redirect('open_show_restaurant')


def delete_restaurant(request, restaurant_id):
    if not _is_admin(request):
        return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.delete()
    return redirect('open_show_restaurant')


def open_update_menu(request, restaurant_id):
    if not _is_admin(request):
        return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList   = restaurant.items.all()
    return render(request, 'delivery/update_menu.html', {"itemList": itemList, "restaurant": restaurant})


def update_menu(request, restaurant_id):
    if not _is_admin(request):
        return redirect('open_signin')
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        name        = request.POST.get('name')
        description = request.POST.get('description')
        price       = request.POST.get('price')
        vegeterian  = request.POST.get('vegeterian') == 'on'
        picture     = request.POST.get('picture')
        if Item.objects.filter(name__iexact=name, restaurant=restaurant).exists():
            return HttpResponse("Duplicate item in this restaurant!")
        Item.objects.create(
            restaurant  = restaurant,
            name        = name,
            description = description,
            price       = price,
            vegeterian  = vegeterian,
            picture     = picture,
        )
    return redirect('open_update_menu', restaurant_id=restaurant_id)


# Admin login (separate from customer signin)
def admin_signin(request):
    error = None
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            request.session['is_admin']   = True
            request.session['admin_name'] = user.username
            return redirect('admin_home')
        error = "Invalid admin credentials."
    return render(request, 'delivery/admin_signin.html', {'error': error})


def admin_logout(request):
    request.session.flush()
    return redirect('index')

# ── Offers Dashboard ─────────────────────────────────
def offers(request, username):
    customer = get_logged_in_customer(request)
    if not customer or customer.username != username:
        return redirect('open_signin')
    
    # Get all active offers
    active_offers = Offer.objects.filter(is_active=True).order_by('-discount_value')
    
    # Prepare categories of offers for the UI
    featured_offers = active_offers[:2]
    all_offers = active_offers[2:]

    return render(request, 'delivery/offers.html', {
        'username': username,
        'customer': customer,
        'featured_offers': featured_offers,
        'all_offers': all_offers
    })

def apply_promo(request, username):
    customer = get_logged_in_customer(request)
    if not customer or customer.username != username:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})

    code = request.GET.get('code', '').strip().upper()
    cart_total = request.GET.get('total', '0')
    try:
        cart_total = float(cart_total)
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid cart total'})

    try:
        offer = Offer.objects.get(code=code, is_active=True)
    except Offer.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid or expired promo code'})

    if cart_total < offer.min_cart_value:
        return JsonResponse({'success': False, 'message': f'Minimum order value must be ₹{offer.min_cart_value}'})

    discount = 0.0
    if offer.discount_type == 'flat':
        discount = offer.discount_value
    elif offer.discount_type == 'percentage':
        discount = (offer.discount_value / 100.0) * cart_total
        if offer.max_discount and discount > offer.max_discount:
            discount = offer.max_discount

    return JsonResponse({
        'success': True,
        'message': f'Promo code applied successfully!',
        'discount': round(discount, 2),
        'code': offer.code,
        'title': offer.title
    })

from .models import Customer, Restaurant, Item, Cart, Order, Offer, DiningRestaurant, DiningTable, Reservation, DiningOffer, DiningCategory, DiningCollection

# ── Dining Views ───────────────────────────────────────
@login_required_view
def dining_home(request, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dining_home', username=customer.username)
        
    categories = DiningCategory.objects.filter(is_active=True).order_by('display_order')
    collections = DiningCollection.objects.filter(active=True).order_by('display_order')
    
    # Query parameters for search/filtering
    query = request.GET.get('q', '')
    cat_slug = request.GET.get('category', '')
    
    restaurants = DiningRestaurant.objects.filter(dining_enabled=True)
    
    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query) | Q(cuisine__icontains=query) | Q(address__icontains=query)
        )
    if cat_slug:
        restaurants = restaurants.filter(categories__slug=cat_slug)
        
    trending_restaurants = DiningRestaurant.objects.filter(dining_enabled=True, trending=True)
        
    return render(request, 'delivery/dining_home.html', {
        'username': username,
        'categories': categories,
        'collections': collections,
        'restaurants': restaurants,
        'trending_restaurants': trending_restaurants,
        'query': query,
        'cat_slug': cat_slug
    })

@login_required_view
def dining_restaurant(request, restaurant_id, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dining_restaurant', restaurant_id=restaurant_id, username=customer.username)
    restaurant = get_object_or_404(DiningRestaurant, id=restaurant_id)
    active_offers = restaurant.dining_offers.filter(active=True)
    
    return render(request, 'delivery/dining_restaurant.html', {
        'username': username,
        'restaurant': restaurant,
        'active_offers': active_offers
    })

@login_required_view
def book_table(request, restaurant_id, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    if request.method == 'POST':
        try:
            from django.urls import reverse
            data = json.loads(request.body)
            date = data.get('date')
            time = data.get('time')
            guests = int(data.get('guests', 2))
            occasion = data.get('occasion', '')
            special_request = data.get('special_request', '')
            
            restaurant = get_object_or_404(DiningRestaurant, id=restaurant_id)
            
            tables = DiningTable.objects.filter(restaurant=restaurant, seats__gte=guests, availability=True).order_by('seats')
            if not tables.exists():
                return JsonResponse({'success': False, 'message': 'No tables available for this guest count.'})
            
            table = tables.first()
            
            request.session['pending_reservation'] = {
                'restaurant_id': restaurant.id,
                'table_id': table.id,
                'date': date,
                'time': time,
                'guests': guests,
                'occasion': occasion,
                'special_request': special_request,
                'reservation_fee': 500.0  # Base fee
            }
            
            redirect_url = reverse('dining_review', args=[username])
            return JsonResponse({'success': True, 'message': 'Redirecting to review...', 'redirect': redirect_url})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required_view
def dining_review(request, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('dining_home', username=customer.username)
        
    pending = request.session.get('pending_reservation')
    if not pending:
        return redirect('dining_home', username=username)
        
    restaurant = get_object_or_404(DiningRestaurant, id=pending['restaurant_id'])
    
    fee = float(pending['reservation_fee'])
    platform_fee = 50.0
    tax = (fee + platform_fee) * 0.18
    total = fee + platform_fee + tax
    
    context = {
        'username': username,
        'restaurant': restaurant,
        'pending': pending,
        'fee': fee,
        'platform_fee': platform_fee,
        'tax': round(tax, 2),
        'total': round(total, 2)
    }
    return render(request, 'delivery/dining_review.html', context)

@login_required_view
def my_reservations(request, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('my_reservations', username=customer.username)
    reservations = Reservation.objects.filter(user=customer).order_by('-booking_date', '-booking_time')
    return render(request, 'delivery/my_reservations.html', {
        'username': username,
        'reservations': reservations,
    })

@login_required_view
def cancel_reservation(request, reservation_id, username):
    customer = get_logged_in_customer(request)
    if customer.username != username:
        return redirect('my_reservations', username=customer.username)
    reservation = get_object_or_404(Reservation, id=reservation_id, user=customer)
    reservation.status = 'cancelled'
    reservation.save()
    return redirect('my_reservations', username=username)
