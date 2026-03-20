# pyre-ignore-all-errors
from django.db import models # pyre-ignore

from django.contrib.auth.models import User # pyre-ignore
from django.db.models.signals import post_save # pyre-ignore
from django.dispatch import receiver # pyre-ignore




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True)   # ADD THIS
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    
    # Leaderboard Stats
    total_score = models.IntegerField(default=0)
    quizzes_completed = models.IntegerField(default=0)
    avg_accuracy = models.FloatField(default=0.0)
    highest_streak = models.IntegerField(default=0)
    show_on_leaderboard = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    
class Category(models.Model):
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=50, blank=True)  # optional icon field

class Subcategory(models.Model):
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=50, blank=True)  # optional
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')

class UserCategoryStats(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    total_score = models.IntegerField(default=0)
    quizzes_completed = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'category')



