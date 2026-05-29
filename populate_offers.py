import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_buddy.settings')
django.setup()

from delivery.models import Offer

Offer.objects.all().delete()

offers = [
    {
        'title': '₹150 OFF on Premium Orders',
        'code': 'MEAL150',
        'discount_type': 'flat',
        'discount_value': 150.0,
        'min_cart_value': 499.0,
        'description': 'Valid on orders above ₹499'
    },
    {
        'title': '40% OFF First Order',
        'code': 'WELCOME40',
        'discount_type': 'percentage',
        'discount_value': 40.0,
        'min_cart_value': 199.0,
        'max_discount': 120.0,
        'description': 'Up to ₹120 OFF for new users'
    },
    {
        'title': 'FREE Delivery',
        'code': 'FREEDEL',
        'discount_type': 'flat',
        'discount_value': 50.0,
        'min_cart_value': 299.0,
        'description': 'Save on delivery fees'
    },
    {
        'title': 'Midnight Cravings: 20% OFF',
        'code': 'NIGHTOWL',
        'discount_type': 'percentage',
        'discount_value': 20.0,
        'min_cart_value': 399.0,
        'max_discount': 100.0,
        'description': 'Valid from 11 PM to 3 AM'
    }
]

for data in offers:
    Offer.objects.create(**data)

print("Offers populated successfully.")
