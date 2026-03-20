from django.urls import path # pyre-ignore
from . import views # pyre-ignore

urlpatterns = [
    path('', views.category_list, name='quiz-categories'),
    path('take/', views.take_quiz, name='take_quiz'),
    path('take/<int:attempt_id>/', views.resume_quiz, name='resume_quiz'),
    path('submit/<int:attempt_id>/', views.submit_quiz, name='submit_quiz'),
    path('save_progress/<int:attempt_id>/', views.save_progress, name='save_progress'),
    path('abandon/<int:attempt_id>/', views.abandon_quiz, name='abandon_quiz'),
    path('result/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
]
