import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def fix_migrations():
    with connection.cursor() as cursor:
        # Delete the quizzes initial migration from history so we can re-apply everything consistently
        cursor.execute("DELETE FROM django_migrations WHERE app = 'quizzes' AND name = '0001_initial'")
        print("Deleted 'quizzes.0001_initial' from migration history.")
        
        # Also cleanup any other weird stuff if needed
        # We'll just start fresh for dashboard and quizzes
        cursor.execute("DELETE FROM django_migrations WHERE app = 'dashboard'")
        cursor.execute("DELETE FROM django_migrations WHERE app = 'users'")
        print("Cleaned up dashboard and users migration history.")

if __name__ == "__main__":
    fix_migrations()
