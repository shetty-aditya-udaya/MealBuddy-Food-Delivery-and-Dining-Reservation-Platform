from django.contrib import admin
from .models import Customer, Restaurant, Item, Cart, Order, Offer, DiningRestaurant, DiningTable, Reservation, DiningOffer, DiningCategory, DiningCollection

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'mobile', 'address')
    search_fields = ('username', 'email')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine', 'rating')
    search_fields = ('name', 'cuisine')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'price', 'vegeterian')
    list_filter  = ('vegeterian', 'restaurant')
    search_fields = ('name',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('customer',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'customer', 'total_price', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('customer__username',)
    readonly_fields = ('created_at',)

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'discount_type', 'discount_value', 'is_active')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code', 'title')

@admin.register(DiningCategory)
class DiningCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'is_featured', 'is_active')
    list_filter = ('is_featured', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(DiningRestaurant)
class DiningRestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine', 'rating', 'total_tables', 'dining_enabled', 'featured', 'trending')
    list_filter = ('dining_enabled', 'featured', 'trending', 'city')
    search_fields = ('name', 'cuisine', 'city')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(DiningCollection)
class DiningCollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'featured', 'active', 'display_order')
    list_filter = ('featured', 'active')

@admin.register(DiningTable)
class DiningTableAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'table_number', 'seats', 'availability')
    list_filter = ('availability', 'restaurant')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'restaurant', 'booking_date', 'booking_time', 'guests', 'status')
    list_filter = ('status', 'booking_date')

@admin.register(DiningOffer)
class DiningOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'restaurant', 'discount_percent', 'active')
    list_filter = ('active', 'restaurant')