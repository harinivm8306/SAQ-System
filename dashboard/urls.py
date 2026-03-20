# pyre-ignore-all-errors
from django.urls import path # pyre-ignore
from . import views # pyre-ignore

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("", views.dashboard, name="dashboard"),
    path('categories/', views.categories_view, name='categories'),
path('subcategories/<int:category_id>/', views.subcategories_view, name='subcategories'),
        path('quiz-settings/<int:subcategory_id>/', views.quiz_settings_view, name='quiz_settings'),
    path('generating-quiz/', views.start_quiz, name='start_quiz'),
    path('api/generate-quiz/', views.generate_quiz_api, name='generate_quiz_api'),
    path('my-quizzes/', views.my_quizzes_view, name='my_quizzes'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
