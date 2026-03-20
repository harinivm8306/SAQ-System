from django.db import models # pyre-ignore
from django.contrib.auth.models import User # pyre-ignore
from django.utils import timezone # pyre-ignore
from dashboard.models import Subcategory # pyre-ignore

class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    timer_enabled = models.BooleanField(default=False)
    timer_duration = models.IntegerField(null=True, blank=True)
    learning_resources = models.JSONField(null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.subcategory.name} - {self.started_at}"

class QuizQuestion(models.Model):
    attempt = models.ForeignKey(QuizAttempt, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    options = models.JSONField()  # ["A", "B", "C", "D"]
    correct_answer = models.CharField(max_length=255)
    user_answer = models.CharField(max_length=255, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Q: {self.question_text[:50]}"
