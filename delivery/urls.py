from django.urls import path
from . import views

urlpatterns = [
    # ── Public ──────────────────────────────────────────
    path('',                          views.index,              name='index'),
    path('open_signin',               views.open_signin,        name='open_signin'),
    path('open_signup',               views.open_signup,        name='open_signup'),
    path('signup',                    views.signup,             name='signup'),
    path('signin',                    views.signin,             name='signin'),
    path('logout',                    views.logout,             name='logout'),
    path('signin_success/<str:username>/', views.signin_success, name='signin_success'),

    # ── Customer (login required) ────────────────────────
    path('dashboard/<str:username>/', views.dashboard,          name='dashboard'),
    path('view_menu/<int:restaurant_id>/<str:username>', views.view_menu, name='view_menu'),
    path('add_to_cart/<int:item_id>/<str:username>',    views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/<str:username>', views.remove_from_cart, name='remove_from_cart'),
    path('show_cart/<str:username>',  views.show_cart,          name='show_cart'),
    path('checkout/<str:username>/',  views.checkout,           name='checkout'),
    path('orders/<str:username>/',    views.orders,             name='orders'),
    path('order_history/<str:username>/', views.order_history,  name='order_history'),
    path('offers/<str:username>/',    views.offers,             name='offers'),
    path('apply_promo/<str:username>/', views.apply_promo,      name='apply_promo'),

    # ── Admin auth ───────────────────────────────────────
    path('admin_signin',              views.admin_signin,       name='admin_signin'),
    path('admin_logout',              views.admin_logout,       name='admin_logout'),
    path('admin_home',                views.admin_home,         name='admin_home'),

    # ── Admin restaurant management ──────────────────────
    path('open_add_restaurant',       views.open_add_restaurant,       name='open_add_restaurant'),
    path('add_restaurant',            views.add_restaurant,            name='add_restaurant'),
    path('open_show_restaurant',      views.open_show_restaurant,      name='open_show_restaurant'),
    path('open_update_restaurant/<int:restaurant_id>', views.open_update_restaurant, name='open_update_restaurant'),
    path('update_restaurant/<int:restaurant_id>',      views.update_restaurant,      name='update_restaurant'),
    path('delete_restaurant/<int:restaurant_id>',      views.delete_restaurant,      name='delete_restaurant'),
    path('open_update_menu/<int:restaurant_id>',       views.open_update_menu,       name='open_update_menu'),
    path('update_menu/<int:restaurant_id>',            views.update_menu,            name='update_menu'),

    # ── Dining ───────────────────────────────────────────
    path('dining/<str:username>/', views.dining_home, name='dining_home'),
    path('dining/restaurant/<int:restaurant_id>/<str:username>/', views.dining_restaurant, name='dining_restaurant'),
    path('dining/book/<int:restaurant_id>/<str:username>/', views.book_table, name='book_table'),
    path('dining/review/<str:username>/', views.dining_review, name='dining_review'),
    path('dining/my_reservations/<str:username>/', views.my_reservations, name='my_reservations'),
    path('dining/cancel_reservation/<int:reservation_id>/<str:username>/', views.cancel_reservation, name='cancel_reservation'),
]
