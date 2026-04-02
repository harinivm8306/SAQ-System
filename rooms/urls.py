from django.urls import path
from . import views
from . import live_views

urlpatterns = [
    path('create/', views.create_room_view, name='create_room'),
    path('join/', views.join_room_view, name='join_room'),
    path('detail/<str:room_code>/', views.room_detail, name='room_detail'),
    path('generate-quiz/<str:room_code>/', views.generate_room_quiz_api, name='generate_room_quiz'),
    path('get-questions/<str:room_code>/', views.get_room_questions_api, name='get_room_questions'),
    
    # Live Quiz Endpoints
    path('live/<str:room_code>/', live_views.live_quiz_view, name='live_quiz'),
    path('api/status/<str:room_code>/', live_views.status_api, name='status_api'),
    path('api/start/<str:room_code>/', live_views.next_question_api, name='next_question_api'),
    path('api/answer/<str:room_code>/', live_views.submit_answer_api, name='submit_answer_api'),
    path('report/<str:room_code>/', live_views.download_report, name='download_report'),
]
