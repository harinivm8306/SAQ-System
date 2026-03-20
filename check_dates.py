# pyre-ignore-all-errors
import sys
import os
import django # pyre-ignore

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from quizzes.models import QuizAttempt # pyre-ignore
from django.utils import timezone # pyre-ignore

now = timezone.now()
print(f"Current Server Time: {now}")

attempts = QuizAttempt.objects.all().order_by('-id')[:5]
for a in attempts:
    print(f"ID: {a.id}, Sub: {a.subcategory.name}, Started: {a.started_at}")
