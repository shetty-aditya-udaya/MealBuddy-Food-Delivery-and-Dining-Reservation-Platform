from django.db import models


class Customer(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=128)
    email = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=200)

    def __str__(self):
        return self.username


class Restaurant(models.Model):
    name = models.CharField(max_length=50)
    picture = models.URLField(max_length=200, default='https://designshack.net/wp-content/uploads/Free-Simple-Restaurant-Logo-Template.jpg')
    cuisine = models.CharField(max_length=200)
    rating = models.FloatField()

    def __str__(self):
        return self.name


class Item(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    price = models.FloatField()
    vegeterian = models.BooleanField(default=False)
    picture = models.URLField(max_length=400, default='https://www.indiafilings.com/learn/wp-content/uploads/2024/08/How-to-Start-Food-Business.jpg')

    def __str__(self):
        return self.name


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="cart")
    items = models.ManyToManyField("Item", related_name="carts", blank=True)

    def total_price(self):
        return sum(item.price for item in self.items.all())


class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Order Placed'),
        ('preparing', 'Preparing'),
        ('on_the_way', 'On the Way'),
        ('delivered', 'Delivered'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    items_snapshot = models.TextField()          # JSON snapshot of items at order time
    total_price = models.FloatField()
    address = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')
    created_at = models.DateTimeField(auto_now_add=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}"

    @property
    def items_json(self):
        import json
        try:
            return json.loads(self.items_snapshot)
        except Exception:
            return []

    class Meta:
        ordering = ['-created_at']

class Offer(models.Model):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=20, choices=[('percentage', 'Percentage'), ('flat', 'Flat Amount')])
    discount_value = models.FloatField()
    min_cart_value = models.FloatField(default=0)
    max_discount = models.FloatField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, blank=True, null=True, related_name="offers")
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.title}"

class DiningCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True) # e.g., 'fas fa-heart'
    cover_image = models.URLField(max_length=400, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    theme_color = models.CharField(max_length=20, default="#eab308")
    display_order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

class DiningRestaurant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    logo = models.URLField(max_length=400, blank=True, null=True)
    image = models.URLField(max_length=400, default='https://images.unsplash.com/photo-1517248135467-4c7edcad34c4')
    cover_image = models.URLField(max_length=400, default='https://images.unsplash.com/photo-1517248135467-4c7edcad34c4')
    gallery_images = models.TextField(blank=True, null=True) # JSON or comma separated
    cuisine = models.CharField(max_length=200)
    price_for_two = models.IntegerField(default=1000)
    dining_offer = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    ambience_description = models.TextField(blank=True, null=True)
    opening_time = models.TimeField(default='10:00:00')
    closing_time = models.TimeField(default='23:00:00')
    total_tables = models.IntegerField(default=10)
    dining_enabled = models.BooleanField(default=True)
    rating = models.FloatField(default=4.0)
    total_reviews = models.IntegerField(default=0)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    featured = models.BooleanField(default=False)
    trending = models.BooleanField(default=False)

    live_music = models.BooleanField(default=False)
    rooftop = models.BooleanField(default=False)
    valet_parking = models.BooleanField(default=False)
    outdoor_seating = models.BooleanField(default=False)
    smoking_zone = models.BooleanField(default=False)
    kids_friendly = models.BooleanField(default=False)
    pet_friendly = models.BooleanField(default=False)
    pure_veg = models.BooleanField(default=False)
    serves_alcohol = models.BooleanField(default=False)

    categories = models.ManyToManyField(DiningCategory, related_name="restaurants", blank=True)
    ambience_tags = models.CharField(max_length=200, default="Fine Dining, Romantic")

    def __str__(self):
        return self.name

class DiningCollection(models.Model):
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    banner_image = models.URLField(max_length=400, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    collection_type = models.CharField(max_length=50, blank=True, null=True)
    restaurants = models.ManyToManyField(DiningRestaurant, related_name="collections", blank=True)
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title

class DiningTable(models.Model):
    restaurant = models.ForeignKey(DiningRestaurant, on_delete=models.CASCADE, related_name="tables")
    table_number = models.CharField(max_length=20)
    seats = models.IntegerField(default=2)
    availability = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.restaurant.name} - Table {self.table_number} ({self.seats} seats)"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="reservations")
    restaurant = models.ForeignKey(DiningRestaurant, on_delete=models.CASCADE, related_name="reservations")
    table = models.ForeignKey(DiningTable, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations")
    booking_date = models.DateField()
    booking_time = models.TimeField()
    guests = models.IntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_request = models.TextField(blank=True, null=True)
    occasion = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    booking_reference = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    def __str__(self):
        return f"Res #{self.id} - {self.user.username} at {self.restaurant.name}"

class DiningOffer(models.Model):
    restaurant = models.ForeignKey(DiningRestaurant, on_delete=models.CASCADE, related_name="dining_offers")
    title = models.CharField(max_length=100)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    min_bill = models.IntegerField(default=0)
    discount_percent = models.IntegerField(default=10)
    max_discount = models.IntegerField(blank=True, null=True)
    valid_from = models.DateField(blank=True, null=True)
    valid_till = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)
    expiry = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} at {self.restaurant.name}"