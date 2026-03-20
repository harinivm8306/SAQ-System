from django.shortcuts import render, redirect # pyre-ignore
from django.contrib.auth.decorators import login_required # pyre-ignore
from django.contrib import messages # pyre-ignore
from django.http import JsonResponse # pyre-ignore
from django.db.models import Count, Avg, F, ExpressionWrapper, FloatField, Q, Sum # pyre-ignore
from django.db.models.functions import TruncDate # pyre-ignore
from django.utils import timezone # pyre-ignore
from django.core.paginator import Paginator # pyre-ignore
from datetime import timedelta
import json

from dashboard.models import Category, Subcategory, Profile, UserCategoryStats # pyre-ignore
from dashboard.utils import generate_quiz_questions, update_leaderboard_stats # pyre-ignore
from quizzes.models import QuizAttempt, QuizQuestion # pyre-ignore



def landing_view(request):
    return render(request, 'landing.html')


@login_required
def dashboard(request):
    """
    Optimized user dashboard with DB-level aggregations.
    """
    # Cleanup old incomplete quizzes (older than 30 days)
    cutoff_date = timezone.now() - timedelta(days=30)
    old_attempts = QuizAttempt.objects.filter(user=request.user, is_completed=False, started_at__lt=cutoff_date)
    if old_attempts.exists():
        old_attempts.delete()

    attempts = QuizAttempt.objects.filter(user=request.user, is_completed=True)
    incomplete_attempts_raw = QuizAttempt.objects.filter(user=request.user, is_completed=False).order_by('-started_at')
    incomplete_attempts = []
    
    for attempt_obj in incomplete_attempts_raw:
        answered = attempt_obj.questions.exclude(user_answer__isnull=True).exclude(user_answer="").count()
        percent = int(answered * 100 / attempt_obj.total_questions) if attempt_obj.total_questions > 0 else 0
        attempt_obj.completion_percent = percent
        if percent < 100:
            incomplete_attempts.append(attempt_obj)
        
    # Efficient count aggregation
    stats = attempts.aggregate(
        total_count=Count('id'),
        avg_score_raw=Avg(
            ExpressionWrapper(
                F('score') * 100.0 / F('total_questions'),
                output_field=FloatField()
            )
        )
    )
    
    total_attempts = stats['total_count'] or 0
    avg_score = round(stats['avg_score_raw'], 1) if stats['avg_score_raw'] is not None else 0
    quizzes_taken = attempts.values('subcategory').distinct().count()

    # Optimized Heatmap Data
    heatmap_data = attempts.annotate(day=TruncDate('started_at')) \
                          .values('day') \
                          .annotate(count=Count('id'))
    
    heatmap_dict = {str(item['day']): item['count'] for item in heatmap_data}

    # Participation Graph Data (Exact last 15 days)
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=14)
    participation_query = attempts.filter(started_at__date__gte=start_date) \
                                 .annotate(day=TruncDate('started_at')) \
                                 .values('day') \
                                 .annotate(count=Count('id')) \
                                 .order_by('day')
    
    participation_labels = []
    participation_values = []
    day_map = {item['day']: item['count'] for item in participation_query}
    
    for i in range(15):
        d = start_date + timedelta(days=i)
        participation_labels.append(d.strftime("%b %d"))
        participation_values.append(day_map.get(d, 0))

    context = {
        'total_attempts': total_attempts,
        'quizzes_taken': quizzes_taken,
        'avg_score': avg_score,
        'heatmap_json': json.dumps(heatmap_dict),
        'participation_labels': json.dumps(participation_labels),
        'participation_values': json.dumps(participation_values),
        'total_active_days': len(heatmap_dict),
        'incomplete_attempts': incomplete_attempts,
    }
    return render(request, "dashboard/dashboard.html", context)

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name")
        profile.bio = request.POST.get("bio")
        profile.show_on_leaderboard = 'show_on_leaderboard' in request.POST

        if request.FILES.get("avatar"):
            profile.avatar = request.FILES.get("avatar")

        profile.save()
        messages.success(request, 'Your profile was successfully updated!')
        return redirect("profile")

    return render(request, "dashboard/profile.html", {"profile": profile})

def create_default_data():
    academic, _ = Category.objects.get_or_create(name="Academic", defaults={'icon': '🎓'})
    entertainment, _ = Category.objects.get_or_create(name="Entertainment", defaults={'icon': '🎭'})
    gk, _ = Category.objects.get_or_create(name="General Knowledge", defaults={'icon': '🧠'})

    Subcategory.objects.get_or_create(name="Physics", category=academic, defaults={'icon': '⚛️'})
    Subcategory.objects.get_or_create(name="Chemistry", category=academic, defaults={'icon': '🧪'})
    Subcategory.objects.get_or_create(name="Biology", category=academic, defaults={'icon': '🧬'})
    Subcategory.objects.get_or_create(name="Computer Networks", category=academic, defaults={'icon': '🌐'})
    Subcategory.objects.get_or_create(name="OOPS", category=academic, defaults={'icon': '🧱'})
    Subcategory.objects.get_or_create(name="DSA", category=academic, defaults={'icon': '📊'})

    Subcategory.objects.get_or_create(name="Movies", category=entertainment, defaults={'icon': '🎬'})
    Subcategory.objects.get_or_create(name="Music", category=entertainment, defaults={'icon': '🎵'})

    Subcategory.objects.get_or_create(name="Current Affairs", category=gk, defaults={'icon': '📰'})
    Subcategory.objects.get_or_create(name="History", category=gk, defaults={'icon': '📜'})


@login_required
def categories_view(request):
    if not Category.objects.exists():
        create_default_data()
    # Also ensure Academic has all subcategories if it exists
    academic = Category.objects.filter(name="Academic").first()
    if academic:
        Subcategory.objects.get_or_create(name="Biology", category=academic, defaults={'icon': '🧬'})
        Subcategory.objects.get_or_create(name="Computer Networks", category=academic, defaults={'icon': '🌐'})
        Subcategory.objects.get_or_create(name="OOPS", category=academic, defaults={'icon': '🧱'})
        Subcategory.objects.get_or_create(name="DSA", category=academic, defaults={'icon': '📊'})

    categories = Category.objects.all()
    return render(request, 'dashboard/categories.html', {'categories': categories})

def subcategories_view(request, category_id):
    category = Category.objects.get(id=category_id)
    subcategories = category.subcategories.all()
    return render(request, 'dashboard/subcategories.html', {'category': category, 'subcategories': subcategories})



def quiz_settings_view(request, subcategory_id):
    subcategory = Subcategory.objects.get(id=subcategory_id)

    if request.method == "POST":
        timer_duration = request.POST.get('timer_duration')
        try:
            timer_duration = int(timer_duration) if timer_duration else 0
        except ValueError:
            timer_duration = 0
            
        # Store settings in session
        request.session['quiz_settings'] = {
            'subcategory_id': subcategory.id,
            'subcategory_name': subcategory.name,
            'difficulty': request.POST.get('difficulty'),
            'num_questions': request.POST.get('num_questions'),
            'timer_enabled': request.POST.get('timer') == 'on',
            'timer_duration': timer_duration,
            'ai_comments': request.POST.get('ai_comments')
        }
        return redirect('start_quiz')  # redirect to actual quiz page

    return render(request, 'dashboard/quiz_settings.html', {'subcategory': subcategory})

@login_required
def start_quiz(request):
    """
    Serves the loading page with the scanner animation.
    The actual AI call will be triggered via AJAX to 'generate_quiz_api'.
    """
    settings = request.session.get('quiz_settings', {})
    if not settings:
        return redirect('categories')
    
    return render(request, 'dashboard/generating_quiz.html', {'settings': settings})

@login_required
def generate_quiz_api(request):
    """
    AJAX endpoint to trigger Gemini quiz generation.
    """
    settings = request.session.get('quiz_settings', {})
    if not settings:
        return JsonResponse({'error': 'No settings found'}, status=400)
    
    subcategory = Subcategory.objects.get(id=settings['subcategory_id'])
    
    # Call Gemini
    result = generate_quiz_questions(
        topic=subcategory.name,
        difficulty=settings['difficulty'],
        count=settings['num_questions'],
        extra_comments=settings.get('ai_comments', "")
    )
    
    if result and 'questions' in result:
        # Store questions and resources in session
        request.session['generated_quiz_data'] = result
        return JsonResponse({'status': 'success', 'redirect_url': '/quizzes/take/'})
    else:
        return JsonResponse({'error': 'Failed to generate quiz. Please try again.'}, status=500)

@login_required
def my_quizzes_view(request):
    """
    Shows a history of all quiz attempts by the user with filtering, sorting, and pagination.
    """
    # Fetch all user attempts and annotate with progress
    all_attempts = QuizAttempt.objects.filter(user=request.user).annotate(
        answered_count=Count('questions', filter=Q(questions__user_answer__isnull=False) & ~Q(questions__user_answer=""))
    )
    
    # Automatically mark 100% quizzes as completed if they weren't submitted officially
    to_fix = all_attempts.filter(is_completed=False, answered_count=F('total_questions'), total_questions__gt=0).prefetch_related('questions')
    attempts_to_update = []
    questions_to_update = []
    
    for att in to_fix:
        # Calculate score
        score = 0
        qs = list(att.questions.all()) # type: ignore # pyre-ignore
        for q in qs:
            if q.user_answer == q.correct_answer:
                q.is_correct = True # pyre-ignore
                score += 1 # pyre-ignore
            else:
                q.is_correct = False
            questions_to_update.append(q)
            
        att.score = score # pyre-ignore
        att.is_completed = True # pyre-ignore
        attempts_to_update.append(att)
        
    if questions_to_update:
        QuizQuestion.objects.bulk_update(questions_to_update, ['is_correct'])
        
    if attempts_to_update:
        QuizAttempt.objects.bulk_update(attempts_to_update, ['score', 'is_completed'])
        for att in attempts_to_update:
            update_leaderboard_stats(request.user, att)

    # Now filter for only completed attempts for the history view
    attempts = QuizAttempt.objects.filter(user=request.user, is_completed=True).select_related('subcategory', 'subcategory__category')

    # Search by topic (Subcategory name)
    search_query = request.GET.get('q', '')
    if search_query:
        attempts = attempts.filter(subcategory__name__icontains=search_query)

    # Filter by Category
    category_id = request.GET.get('category', '')
    if category_id:
        attempts = attempts.filter(subcategory__category_id=category_id)

    # Filter by Subcategory
    subcategory_id = request.GET.get('subcategory', '')
    if subcategory_id:
        attempts = attempts.filter(subcategory_id=subcategory_id)

    # Filter by Date range
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if start_date:
        attempts = attempts.filter(started_at__date__gte=start_date)
    if end_date:
        attempts = attempts.filter(started_at__date__lte=end_date)

    # Sorting
    sort_by = request.GET.get('sort', '-started_at')
    # Valid sort options
    if sort_by in ['-started_at', 'started_at', '-score', 'score', 'subcategory__name', '-subcategory__name']:
        attempts = attempts.order_by(sort_by)
    else:
        attempts = attempts.order_by('-started_at')

    # Pagination
    paginator = Paginator(attempts, 8) # 8 quizzes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'subcategories': subcategories,
        'search_query': search_query,
        'current_category': category_id,
        'current_subcategory': subcategory_id,
        'start_date': start_date,
        'end_date': end_date,
        'current_sort': sort_by,
    }
    return render(request, 'dashboard/my_quizzes.html', context)

@login_required
def leaderboard_view(request):
    """
    Shows top performers globally and by category.
    """
    leaderboard_type = request.GET.get('type', 'global')
    category_id = request.GET.get('category', '')
    
    users_list = []
    current_user_stat = None
    
    categories = Category.objects.all()
    selected_cat_id = None
    
    try:
        if leaderboard_type == 'category' and category_id:
            # Category leaderboard
            selected_category = Category.objects.get(id=category_id)
            selected_cat_id = selected_category.id
            users_stats = UserCategoryStats.objects.filter(category=selected_category) \
                                                 .select_related('user', 'user__profile') \
                                                 .filter(user__profile__show_on_leaderboard=True) \
                                                 .order_by('-total_score', '-quizzes_completed')[:50]
            
            for i, stat in enumerate(users_stats):
                user_data = {
                    'rank': i + 1,
                    'username': stat.user.username,
                    'initial': stat.user.username[0].upper() if stat.user.username else '?',
                    'full_name': stat.user.profile.full_name or stat.user.username,
                    'score': stat.total_score,
                    'score_display': f"{stat.total_score} pts",
                    'accuracy': stat.user.profile.avg_accuracy,
                    'quizzes': stat.quizzes_completed,
                    'avatar': stat.user.profile.avatar,
                    'is_current': stat.user == request.user,
                }
                users_list.append(user_data)
                if stat.user == request.user:
                    current_user_stat = user_data
        elif leaderboard_type == 'streaks':
            # Highest Streaks leaderboard
            profiles = Profile.objects.filter(show_on_leaderboard=True) \
                                      .select_related('user') \
                                      .order_by('-highest_streak', '-total_score')[:50]
            
            for i, p in enumerate(profiles):
                user_data = {
                    'rank': i + 1,
                    'username': p.user.username,
                    'initial': p.user.username[0].upper() if p.user.username else '?',
                    'full_name': p.full_name or p.user.username,
                    'score': p.highest_streak, 
                    'score_display': f"{p.highest_streak} 🔥",
                    'accuracy': p.avg_accuracy,
                    'quizzes': p.quizzes_completed,
                    'avatar': p.avatar,
                    'is_current': p.user == request.user,
                }
                users_list.append(user_data)
                if p.user == request.user:
                    current_user_stat = user_data
        else:
            # Global leaderboard
            profiles = Profile.objects.filter(show_on_leaderboard=True) \
                                      .select_related('user') \
                                      .order_by('-total_score', '-avg_accuracy')[:50]
            
            for i, p in enumerate(profiles):
                user_data = {
                    'rank': i + 1,
                    'username': p.user.username,
                    'initial': p.user.username[0].upper() if p.user.username else '?',
                    'full_name': p.full_name or p.user.username,
                    'score': p.total_score,
                    'score_display': f"{p.total_score} pts",
                    'accuracy': p.avg_accuracy,
                    'quizzes': p.quizzes_completed,
                    'avatar': p.avatar,
                    'is_current': p.user == request.user,
                }
                users_list.append(user_data)
                if p.user == request.user:
                    current_user_stat = user_data
    except (Category.DoesNotExist, ValueError):
        leaderboard_type = 'global' # Reset on error

    context = {
        'leaderboard': users_list,
        'categories': categories,
        'current_type': leaderboard_type,
        'selected_category': selected_cat_id,
        'current_user_stat': current_user_stat
    }
    return render(request, 'dashboard/leaderboard.html', context)
