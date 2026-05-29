from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'delivery'

    def ready(self):
        # Temporary automated superuser creation logic
        import os
        from django.contrib.auth.models import User
        from django.db import connection

        if "auth_user" in connection.introspection.table_names():
            try:
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_superuser(
                        username='admin',
                        email='admin@gmail.com',
                        password='admin123'
                    )
                    print("--- Production Superuser 'admin' created successfully! ---")
            except Exception as e:
                print(f"Error creating superuser during startup: {e}")
