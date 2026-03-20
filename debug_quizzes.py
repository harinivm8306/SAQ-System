# pyre-ignore-all-errors
import os
import django # pyre-ignore

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from quizzes.models import QuizAttempt # pyre-ignore
from django.contrib.auth.models import User # pyre-ignore

user = User.objects.first() # Assume first user for now, or all users
if user:
    print(f"User: {user.username}")
    all_attempts = QuizAttempt.objects.filter(user=user)
    print(f"Total attempts: {all_attempts.count()}")
    completed_attempts = all_attempts.filter(is_completed=True)
    print(f"Completed (is_completed=True): {completed_attempts.count()}")
    incomplete_attempts = all_attempts.filter(is_completed=False)
    print(f"Incomplete (is_completed=False): {incomplete_attempts.count()}")
    
    for att in all_attempts:
        answered = att.questions.exclude(user_answer__isnull=True).exclude(user_answer="").count()
        percent = int(answered * 100 / att.total_questions) if att.total_questions > 0 else 0
        print(f"ID: {att.id}, Sub: {att.subcategory.name}, Completed: {att.is_completed}, Progress: {percent}%")
else:
    print("No users found")
