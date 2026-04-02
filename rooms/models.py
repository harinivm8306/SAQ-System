import random
import string
from django.db import models
from django.contrib.auth.models import User

def generate_room_code():
    return ''.join(random.choices(string.digits, k=8))

class Room(models.Model):
    code = models.CharField(max_length=8, unique=True, default=generate_room_code)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    topic = models.CharField(max_length=255)
    
    # Question Patterns
    pattern_mcq = models.BooleanField(default=True)
    pattern_match = models.BooleanField(default=False)
    pattern_typing = models.BooleanField(default=False)
    pattern_arrange = models.BooleanField(default=False)
    
    # AI questions data (JSON) - Store generated questions here
    questions_data = models.JSONField(null=True, blank=True)
    
    # Live Quiz State
    status = models.CharField(max_length=20, default='waiting') # waiting, active, leaderboard, finished
    current_question_index = models.IntegerField(default=0)
    timer_end = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.code} - {self.topic}"

class RoomMember(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')

    def __str__(self):
        return f"{self.user.username} in Room {self.room.code}"

class RoomAnswer(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question_index = models.IntegerField()
    is_correct = models.BooleanField(default=False)
    points = models.IntegerField(default=0)
    time_taken = models.FloatField(default=0.0)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('room', 'user', 'question_index')
