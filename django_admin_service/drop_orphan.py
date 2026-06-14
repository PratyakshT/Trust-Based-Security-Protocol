import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_admin_service.settings')
django.setup()

from django.db import connection, transaction

with connection.cursor() as cursor:
    cursor.execute("DROP TABLE IF EXISTS network_state_siotnode_friends CASCADE;")
    print("Dropped orphaned table network_state_siotnode_friends")

transaction.commit()
